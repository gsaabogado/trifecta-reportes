"""
Google Drive folder downloader for Trifecta CCI Report Generator.

Downloads a shared Google Drive folder (including Shared Drives) to a local
temp directory, preserving the folder structure.

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

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Scopes needed
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Token cache location
TOKEN_PATH = Path(__file__).resolve().parent.parent / ".gdrive_token.json"
CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "credentials.json"


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

    # 6. Last resort: try gcloud ADC file directly with token refresh
    adc_path = Path.home() / ".config/gcloud/application_default_credentials.json"
    if adc_path.exists():
        import json
        with open(adc_path) as f:
            adc = json.load(f)
        # Create credentials from ADC and request Drive scope
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
    # Match: https://drive.google.com/drive/folders/FOLDER_ID?...
    # Also: https://drive.google.com/drive/u/0/folders/FOLDER_ID
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url_or_id)
    if match:
        return match.group(1)
    # Already a raw ID?
    if re.match(r'^[a-zA-Z0-9_-]{10,}$', url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract folder ID from: {url_or_id}")


def download_folder(service, folder_id, local_dir, depth=0):
    """Recursively download a Google Drive folder."""
    indent = "  " * depth

    # List all items in the folder
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType, size)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=1000,
    ).execute()

    items = results.get("files", [])
    folders = [f for f in items if f["mimeType"] == "application/vnd.google-apps.folder"]
    files = [f for f in items if f["mimeType"] != "application/vnd.google-apps.folder"]

    print(f"{indent}📁 {local_dir.name}/ ({len(files)} files, {len(folders)} subfolders)")

    # Download files
    for file_info in files:
        file_path = local_dir / file_info["name"]
        print(f"{indent}  ↓ {file_info['name']}")

        # Skip Google Docs native formats (Sheets, Docs, etc.)
        if file_info["mimeType"].startswith("application/vnd.google-apps."):
            # Export Google Docs as their Office equivalents
            export_map = {
                "application/vnd.google-apps.document": (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
                "application/vnd.google-apps.spreadsheet": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
            }
            if file_info["mimeType"] in export_map:
                mime, ext = export_map[file_info["mimeType"]]
                request = service.files().export_media(fileId=file_info["id"], mimeType=mime)
                file_path = file_path.with_suffix(ext)
            else:
                print(f"{indent}    (skipped: {file_info['mimeType']})")
                continue
        else:
            request = service.files().get_media(
                fileId=file_info["id"],
                supportsAllDrives=True,
            )

        buf = BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        file_path.write_bytes(buf.getvalue())

    # Recurse into subfolders
    for folder_info in sorted(folders, key=lambda f: f["name"]):
        subfolder_path = local_dir / folder_info["name"]
        subfolder_path.mkdir(parents=True, exist_ok=True)
        download_folder(service, folder_info["id"], subfolder_path, depth + 1)


def download_gdrive_folder(url_or_id, output_dir=None):
    """
    Download a Google Drive folder to a local directory.

    Args:
        url_or_id: Google Drive folder URL or folder ID
        output_dir: Where to download. If None, creates a temp directory.

    Returns:
        Path to the downloaded folder.
    """
    folder_id = extract_folder_id(url_or_id)
    print(f"Folder ID: {folder_id}")

    # Authenticate
    print("Authenticating with Google Drive...")
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    # Get folder name
    folder_meta = service.files().get(
        fileId=folder_id,
        fields="name",
        supportsAllDrives=True,
    ).execute()
    folder_name = folder_meta["name"]
    print(f"Folder name: {folder_name}")

    # Create output directory
    if output_dir:
        local_dir = Path(output_dir)
    else:
        local_dir = Path(tempfile.mkdtemp()) / folder_name
    local_dir.mkdir(parents=True, exist_ok=True)

    # Download
    print(f"Downloading to: {local_dir}")
    download_folder(service, folder_id, local_dir)
    print(f"\nDone! Downloaded to: {local_dir}")

    return str(local_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Google Drive folder")
    parser.add_argument("url", help="Google Drive folder URL or ID")
    parser.add_argument("-o", "--output", help="Output directory", default=None)
    args = parser.parse_args()
    download_gdrive_folder(args.url, args.output)
