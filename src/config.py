"""
Centralized configuration and secrets handling.

The Streamlit app may be deployed in three different contexts:
  1. Streamlit Community Cloud  → secrets in `st.secrets`
  2. Local dev with `.streamlit/secrets.toml` → also in `st.secrets`
  3. Local dev without secrets   → only "local folder path" mode is available

This module exposes a single `Settings` object that knows which providers are
configured and produces friendly user messages when something is missing.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import streamlit as st

APP_VERSION = "0.2.0"


def _get_secret(key: str) -> Optional[str]:
    """Read a secret from st.secrets, falling back to env vars. Never raises."""
    # 1. Streamlit secrets
    try:
        if key in st.secrets:
            value = st.secrets[key]
            return str(value) if value is not None else None
    except Exception:
        # st.secrets may raise if no secrets file exists at all
        pass
    # 2. Environment variable
    return os.environ.get(key)


@dataclass(frozen=True)
class Settings:
    gdrive_sa_json: Optional[str]
    dropbox_access_token: Optional[str]
    dropbox_refresh_token: Optional[str]
    dropbox_app_key: Optional[str]
    dropbox_app_secret: Optional[str]
    allow_local_path: bool

    @property
    def has_gdrive(self) -> bool:
        return bool(self.gdrive_sa_json)

    @property
    def has_dropbox(self) -> bool:
        # Either a long-lived access token (legacy) or refresh-token trio works
        if self.dropbox_access_token:
            return True
        return bool(
            self.dropbox_refresh_token
            and self.dropbox_app_key
            and self.dropbox_app_secret
        )

    def gdrive_sa_info(self) -> dict:
        """Parse the GDrive service account JSON. Raises on bad config."""
        if not self.gdrive_sa_json:
            raise RuntimeError("GDRIVE_SERVICE_ACCOUNT secret is not set.")
        try:
            return json.loads(self.gdrive_sa_json)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                "GDRIVE_SERVICE_ACCOUNT is not valid JSON. "
                "Make sure it is wrapped in TOML triple quotes."
            ) from e


def _is_streamlit_cloud() -> bool:
    """Detect Streamlit Community Cloud.

    Cloud mounts apps under /mount/src/. We also check common env hints.
    """
    if Path("/mount/src").exists():
        return True
    if os.environ.get("HOSTNAME", "").startswith("streamlit"):
        return True
    return False


@st.cache_resource
def load_settings() -> Settings:
    """Load settings once per Streamlit session (cached across reruns)."""
    return Settings(
        gdrive_sa_json=_get_secret("GDRIVE_SERVICE_ACCOUNT"),
        dropbox_access_token=_get_secret("DROPBOX_ACCESS_TOKEN"),
        dropbox_refresh_token=_get_secret("DROPBOX_REFRESH_TOKEN"),
        dropbox_app_key=_get_secret("DROPBOX_APP_KEY"),
        dropbox_app_secret=_get_secret("DROPBOX_APP_SECRET"),
        # Local-path mode only makes sense when running on the user's machine
        allow_local_path=not _is_streamlit_cloud(),
    )
