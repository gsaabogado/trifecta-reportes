"""
Dropbox folder downloader for the Trifecta CCI Report Generator.

Mirrors the design of `gdrive_download.py`:
  - Accepts a Dropbox shared folder link (any user can share with us)
  - Walks the folder recursively, preserving structure
  - Downloads in parallel and compresses images on the fly
  - Returns the local path to the downloaded folder

Auth model
----------
Dropbox does NOT allow listing the contents of a shared link without an
authenticated app. We use a Dropbox App with `files.metadata.read` and
`sharing.read` scopes, and a long-lived access token stored in
`st.secrets["DROPBOX_ACCESS_TOKEN"]`. The token belongs to the Trifecta
account; it is not the link sender's account. The Dropbox API lets that
token traverse arbitrary shared links via the `SharedLink` parameter.

Setup (one time)
----------------
1. https://www.dropbox.com/developers/apps → Create app
2. API: "Scoped access", access type: "Full Dropbox" (or App folder if you
   want to scope to a single folder)
3. Permissions tab → enable: files.metadata.read, files.content.read,
   sharing.read
4. Settings tab → "OAuth 2 / Generated access token" → Generate
5. Copy that token into Streamlit secrets as DROPBOX_ACCESS_TOKEN
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import FileMetadata, FolderMetadata, SharedLink
from PIL import Image


# Image compression settings (kept in sync with gdrive_download.py)
MAX_IMAGE_WIDTH = 800
MAX_IMAGE_HEIGHT = 600
JPEG_QUALITY = 70
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}

MAX_WORKERS = 8


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------
DROPBOX_URL_RE = re.compile(
    r"https?://(?:www\.)?dropbox\.com/(?:scl/fo|sh|s|scl/fi)/[^\s]+",
    re.IGNORECASE,
)


def is_dropbox_url(url: str) -> bool:
    return bool(DROPBOX_URL_RE.match(url.strip()))


def normalize_url(url: str) -> str:
    """Normalize a Dropbox shared link URL.

    The Dropbox API requires the original shared link form. We strip any
    `?dl=0` / `?dl=1` query strings (Dropbox accepts both) and trailing
    whitespace, but otherwise leave the URL alone — including the rlkey
    parameter which is required on the new `scl/fo` shared links.
    """
    url = url.strip()
    # Drop only the dl= query param, keep rlkey and others
    if "?" in url:
        base, _, query = url.partition("?")
        params = [p for p in query.split("&") if p and not p.startswith("dl=")]
        url = base + ("?" + "&".join(params) if params else "")
    return url


# ---------------------------------------------------------------------------
# Image compression (shared with gdrive_download in spirit)
# ---------------------------------------------------------------------------
def _compress_image(data: bytes, file_name: str) -> tuple[bytes, str]:
    try:
        img = Image.open(BytesIO(data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        new_name = Path(file_name).with_suffix(".jpg").name
        return buf.getvalue(), new_name
    except Exception:
        return data, file_name


# ---------------------------------------------------------------------------
# Listing & downloading
# ---------------------------------------------------------------------------
def _strip_share_root(path: str, share_prefix_lower: str) -> str:
    """Strip the share root prefix from a Dropbox path.

    Dropbox returns entry paths in the form ``/<share-root-name>/<sub>/<file>``
    even when those entries came from a shared link listing — but the API
    endpoints (`files_list_folder` and `sharing_get_shared_link_file`) require
    paths *relative to the share root*, prefixed with ``/``. This helper
    converts the former to the latter.

    Returns ``""`` for the share root itself (which the API also accepts as
    "list the root").
    """
    if path.lower() == share_prefix_lower:
        return ""
    if path.lower().startswith(share_prefix_lower + "/"):
        return "/" + path[len(share_prefix_lower) + 1:]
    # Already relative or unexpected format — pass through.
    return path if path.startswith("/") else "/" + path


def _list_shared_folder(
    dbx: dropbox.Dropbox, url: str
) -> tuple[str, list[FileMetadata]]:
    """List every file under a Dropbox shared folder link.

    Recurses manually because Dropbox does not support
    ``recursive=True`` together with ``shared_link``.

    Returns
    -------
    folder_name : str
        Display name of the root shared folder.
    files : list of FileMetadata
        All files under the share, in arbitrary order. Their ``path_display``
        fields include the share root prefix.
    """
    shared_link = SharedLink(url=url)

    try:
        root_meta = dbx.sharing_get_shared_link_metadata(url=url)
    except AuthError as e:
        raise RuntimeError(
            "Dropbox auth failed. Check the refresh token / app key / app secret "
            "in Streamlit Secrets and that the Dropbox app has the scopes: "
            "files.metadata.read, files.content.read, sharing.read."
        ) from e
    except ApiError as e:
        raise RuntimeError(f"Dropbox API rejected the link: {e}") from e

    folder_name = getattr(root_meta, "name", "dropbox_folder")
    share_prefix_lower = "/" + folder_name.lower()

    files: list[FileMetadata] = []

    def walk(rel_path: str) -> None:
        """rel_path is relative to the share root, prefixed with '/' (or '' for root)."""
        try:
            result = dbx.files_list_folder(
                path=rel_path, shared_link=shared_link, recursive=False
            )
        except ApiError as e:
            raise RuntimeError(f"Failed to list {rel_path or '/'}: {e}") from e

        while True:
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    files.append(entry)
                elif isinstance(entry, FolderMetadata):
                    # Skip hidden folders like .claude, .git, etc.
                    if entry.name.startswith("."):
                        continue
                    sub_rel = _strip_share_root(entry.path_lower, share_prefix_lower)
                    walk(sub_rel)
            if not result.has_more:
                break
            result = dbx.files_list_folder_continue(result.cursor)

    walk("")
    return folder_name, files


def _build_client(
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> dropbox.Dropbox:
    """Build a Dropbox client from either an access token or a refresh-token trio."""
    if refresh_token and app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
            timeout=120,
        )
    if access_token:
        return dropbox.Dropbox(access_token, timeout=120)
    raise RuntimeError(
        "Dropbox credentials missing. Need either DROPBOX_ACCESS_TOKEN or "
        "(DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY + DROPBOX_APP_SECRET)."
    )


def _download_one(
    auth: dict,
    url: str,
    share_prefix_lower: str,
    entry: FileMetadata,
) -> tuple[Optional[bytes], str, bool]:
    """Download a single file via the shared link. Returns (bytes, name, is_image)."""
    # Build a per-thread Dropbox client (httplib2-style state isn't shared)
    dbx = _build_client(**auth)

    # sharing_get_shared_link_file wants the path *relative to the share root*
    rel_path = _strip_share_root(entry.path_lower, share_prefix_lower)

    try:
        _meta, resp = dbx.sharing_get_shared_link_file(url=url, path=rel_path)
    except Exception as e:
        raise RuntimeError(f"Could not download {entry.name}: {e}") from e

    data = resp.content
    file_name = entry.name
    is_image = Path(file_name).suffix.lower() in IMAGE_EXTENSIONS
    if is_image:
        data, file_name = _compress_image(data, file_name)
    return data, file_name, is_image


def download_dropbox_folder(
    url: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> str:
    """Download a Dropbox shared folder to a local directory.

    Pass either `access_token` (legacy long-lived) or the trio
    `refresh_token` + `app_key` + `app_secret` (recommended for new apps).

    Args:
        url: Dropbox shared folder URL.
        access_token: Long-lived Dropbox access token (legacy).
        refresh_token: OAuth2 refresh token (preferred).
        app_key: Dropbox app key (paired with refresh_token).
        app_secret: Dropbox app secret (paired with refresh_token).
        output_dir: Where to download. If None, creates a temp directory.
        progress_callback: Optional callback(current, total, filename).

    Returns:
        Path to the downloaded folder.
    """
    if not is_dropbox_url(url):
        raise ValueError(f"Not a Dropbox URL: {url}")

    url = normalize_url(url)
    auth = dict(
        access_token=access_token,
        refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )
    dbx = _build_client(**auth)

    print(f"Listing Dropbox folder...")
    folder_name, entries = _list_shared_folder(dbx, url)
    total = len(entries)
    print(f"Found {total} files")

    if total == 0:
        raise RuntimeError("Shared link contains no files.")

    share_prefix_lower = "/" + folder_name.lower()

    if output_dir:
        local_dir = Path(output_dir)
    else:
        local_dir = Path(tempfile.mkdtemp()) / folder_name
    local_dir.mkdir(parents=True, exist_ok=True)

    def _local_subpath(entry: FileMetadata) -> str:
        """Path under `local_dir` for an entry, preserving subfolder casing."""
        # _strip_share_root takes a lowercased prefix but slices the original
        # string, so we get back an original-case sub-path (e.g. "/2.Photos/...").
        return _strip_share_root(entry.path_display, share_prefix_lower).lstrip("/")

    # Pre-create subdirectories
    for entry in entries:
        rel_local = _local_subpath(entry)
        sub = os.path.dirname(rel_local)
        if sub:
            (local_dir / sub).mkdir(parents=True, exist_ok=True)

    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for entry in entries:
            fut = executor.submit(_download_one, auth, url, share_prefix_lower, entry)
            futures[fut] = entry

        for fut in as_completed(futures):
            entry = futures[fut]
            completed += 1
            try:
                data, file_name, is_image = fut.result()
                if data is not None:
                    rel_local = _local_subpath(entry)
                    sub = os.path.dirname(rel_local)
                    dest = local_dir / sub / file_name if sub else local_dir / file_name
                    dest.write_bytes(data)
                    tag = "IMG" if is_image else "DOC"
                    print(f"  [{completed}/{total}] {tag} {rel_local}")
            except Exception as e:
                print(f"  [{completed}/{total}] ERR {entry.name}: {e}")

            if progress_callback:
                progress_callback(completed, total, entry.name)

    print(f"Done. Downloaded to: {local_dir}")
    return str(local_dir)


# ---------------------------------------------------------------------------
# CLI for local testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download a Dropbox shared folder")
    parser.add_argument("url", help="Dropbox shared folder URL")
    parser.add_argument("-o", "--output", default=None, help="Output directory")
    args = parser.parse_args()

    download_dropbox_folder(
        args.url,
        access_token=os.environ.get("DROPBOX_ACCESS_TOKEN"),
        refresh_token=os.environ.get("DROPBOX_REFRESH_TOKEN"),
        app_key=os.environ.get("DROPBOX_APP_KEY"),
        app_secret=os.environ.get("DROPBOX_APP_SECRET"),
        output_dir=args.output,
    )
