"""
Google Drive folder downloader for Trifecta CCI Report Generator.

Downloads a shared Google Drive folder (including Shared Drives) to a local
temp directory, preserving the folder structure. Images are compressed on
download for speed.

Usage:
    python gdrive_download.py "https://drive.google.com/drive/folders/FOLDER_ID" [-o /output/dir]
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image

# Scopes needed
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Token cache location
TOKEN_PATH = Path(__file__).resolve().parent.parent / ".gdrive_token.json"
CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials.json"

# Image compression settings
MAX_IMAGE_WIDTH = 800   # px — enough for 3.3" at 150dpi in the report
MAX_IMAGE_HEIGHT = 600
JPEG_QUALITY = 70
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

# Parallel download settings
MAX_WORKERS = 8


def get_credentials():
    """Get or refresh Google credentials with Drive read scope."""
    creds = None

    # 1. Try cached token
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # 2. Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            return creds
        except Exception:
            creds = None

    # 3. If valid, use it
    if creds and creds.valid:
        return creds

    # 4. Try Application Default Credentials (gcloud auth)
    try:
        creds, _ = google.auth.default(scopes=SCOPES)
        if creds.valid or hasattr(creds, 'refresh_token'):
            creds.refresh(Request())
            return creds
    except Exception:
        pass

    # 5. OAuth browser flow (requires credentials.json)
    if CREDENTIALS_PATH.exists():
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        creds = flow.run_local_server(port=0)
        _save_token(creds)
        return creds

    # 6. Last resort: try gcloud ADC file directly
    adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
    if adc_path.exists():
        import json
        with open(adc_path) as f:
            adc = json.load(f)
        creds = Credentials(
            token=None,
            refresh_token=adc.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=adc.get("client_id"),
            client_secret=adc.get("client_secret"),
            scopes=SCOPES,
        )
        creds.refresh(Request())
        _save_token(creds)
        return creds

    raise RuntimeError(
        "No Google credentials found. Either:\n"
        "  1. Run: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/drive.readonly\n"
        "  2. Or place a credentials.json (OAuth desktop app) next to this script."
    )


def _save_token(creds):
    """Cache credentials to disk."""
    TOKEN_PATH.write_text(creds.to_json())


def extract_folder_id(url_or_id):
    """Extract folder ID from a Google Drive URL or return as-is if already an ID."""
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{10,}$', url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract folder ID from: {url_or_id}")


def _compress_image(data, file_name):
    """Compress image bytes, return compressed bytes and new filename."""
    try:
        img = Image.open(BytesIO(data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        # Change extension to .jpg
        new_name = Path(file_name).with_suffix(".jpg").name
        return buf.getvalue(), new_name
    except Exception:
        # If compression fails, return original
        return data, file_name


def _download_one_file(creds, file_info):
    """Download a single file. Returns (data_bytes, file_name, is_image)."""
    # Build a per-thread service (httplib2 is not thread-safe)
    service = build("drive", "v3", credentials=creds)

    file_id = file_info["id"]
    file_name = file_info["name"]
    mime = file_info["mimeType"]

    # Handle Google Docs native formats
    if mime.startswith("application/vnd.google-apps."):
        export_map = {
            "application/vnd.google-apps.document": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
            "application/vnd.google-apps.spreadsheet": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        }
        if mime in export_map:
            export_mime, ext = export_map[mime]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            file_name = Path(file_name).with_suffix(ext).name
        else:
            return None, file_name, False
    else:
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)

    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    data = buf.getvalue()
    is_image = Path(file_name).suffix.lower() in IMAGE_EXTENSIONS

    # Compress images on the fly
    if is_image:
        data, file_name = _compress_image(data, file_name)

    return data, file_name, is_image


def _collect_all_files(service, folder_id, rel_path=""):
    """Recursively list all files with their relative paths."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=1000,
    ).execute()

    items = results.get("files", [])
    folders = [f for f in items if f["mimeType"] == "application/vnd.google-apps.folder"]
    files = [f for f in items if f["mimeType"] != "application/vnd.google-apps.folder"]

    # Collect files with their destination path
    all_files = []
    for f in files:
        all_files.append((f, rel_path))

    # Recurse into subfolders
    for folder_info in sorted(folders, key=lambda f: f["name"]):
        sub_path = os.path.join(rel_path, folder_info["name"]) if rel_path else folder_info["name"]
        all_files.extend(_collect_all_files(service, folder_info["id"], sub_path))

    return all_files


def download_folder(service, folder_id, local_dir, depth=0, creds=None, progress_callback=None):
    """Download a Google Drive folder with parallel downloads and compression.

    Args:
        service: Google Drive API service
        folder_id: Drive folder ID
        local_dir: Local directory to download to
        depth: Recursion depth (for logging)
        creds: Credentials for parallel workers
        progress_callback: Optional callback(current, total, filename)
    """
    print(f"Scanning folder structure...")
    all_files = _collect_all_files(service, folder_id)
    total = len(all_files)
    print(f"Found {total} files to download")

    # Create all necessary subdirectories
    subdirs = set()
    for _, rel_path in all_files:
        if rel_path:
            subdirs.add(rel_path)
    for subdir in subdirs:
        (local_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Download in parallel
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_info = {}
        for file_info, rel_path in all_files:
            future = executor.submit(_download_one_file, creds, file_info)
            future_to_info[future] = (file_info, rel_path)

        for future in as_completed(future_to_info):
            file_info, rel_path = future_to_info[future]
            completed += 1

            try:
                data, file_name, is_image = future.result()
                if data is not None:
                    dest = local_dir / rel_path / file_name if rel_path else local_dir / file_name
                    dest.write_bytes(data)
                    tag = "🖼" if is_image else "📄"
                    print(f"  [{completed}/{total}] {tag} {rel_path}/{file_name}" if rel_path
                          else f"  [{completed}/{total}] {tag} {file_name}")
            except Exception as e:
                print(f"  [{completed}/{total}] ❌ {file_info['name']}: {e}")

            if progress_callback:
                progress_callback(completed, total, file_info["name"])


def download_gdrive_folder(url_or_id, output_dir=None, creds=None, progress_callback=None):
    """
    Download a Google Drive folder to a local directory.

    Args:
        url_or_id: Google Drive folder URL or folder ID
        output_dir: Where to download. If None, creates a temp directory.
        creds: Pre-built credentials (for Streamlit). If None, auto-detects.
        progress_callback: Optional callback(current, total, filename)

    Returns:
        Path to the downloaded folder.
    """
    folder_id = extract_folder_id(url_or_id)
    print(f"Folder ID: {folder_id}")

    if creds is None:
        print("Authenticating with Google Drive...")
        creds = get_credentials()

    service = build("drive", "v3", credentials=creds)

    # Get folder name
    folder_meta = service.files().get(
        fileId=folder_id, fields="name", supportsAllDrives=True,
    ).execute()
    folder_name = folder_meta["name"]
    print(f"Folder name: {folder_name}")

    if output_dir:
        local_dir = Path(output_dir)
    else:
        local_dir = Path(tempfile.mkdtemp()) / folder_name
    local_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading to: {local_dir}")
    download_folder(service, folder_id, local_dir, creds=creds,
                    progress_callback=progress_callback)
    print(f"\nDone! Downloaded to: {local_dir}")

    return str(local_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Google Drive folder")
    parser.add_argument("url", help="Google Drive folder URL or ID")
    parser.add_argument("-o", "--output", help="Output directory", default=None)
    args = parser.parse_args()
    download_gdrive_folder(args.url, args.output)
