#!/usr/bin/env python3
"""
One-time Dropbox OAuth setup for the Trifecta CCI Report Generator.

Run this once after creating your Dropbox app. It will:
  1. Ask you for your app key and app secret (from the Dropbox App Console).
  2. Open a browser-friendly authorization URL.
  3. Ask you to paste back the access code Dropbox shows you.
  4. Print the refresh token + the three secrets you need to put into
     Streamlit Cloud Secrets.

Usage:
    python scripts/dropbox_setup.py
"""

from __future__ import annotations

import sys
import textwrap

try:
    from dropbox import DropboxOAuth2FlowNoRedirect
except ImportError:
    sys.exit(
        "The dropbox SDK is not installed. Run:\n"
        "  pip install dropbox\n"
        "and try again."
    )


def prompt(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        sys.exit(f"{label} is required. Aborting.")
    return value


def main() -> None:
    print(textwrap.dedent("""
        ============================================================
          Trifecta CCI Reports — Dropbox OAuth Setup
        ============================================================

        Before you start, you should already have:
          1. Created a Dropbox app at:
             https://www.dropbox.com/developers/apps
          2. Selected: 'Scoped access' + 'Full Dropbox'
          3. On the 'Permissions' tab, enabled THREE scopes:
                - files.metadata.read
                - files.content.read
                - sharing.read
             …and clicked 'Submit'.
          4. On the 'Settings' tab, copied the App key and App secret.
        ------------------------------------------------------------
    """).strip())
    print()

    app_key = prompt("App key")
    app_secret = prompt("App secret")

    auth_flow = DropboxOAuth2FlowNoRedirect(
        app_key,
        app_secret,
        token_access_type="offline",  # ← gives us a refresh_token
    )
    authorize_url = auth_flow.start()

    print()
    print("STEP 1 — Open this URL in your browser and click 'Allow':")
    print()
    print(f"  {authorize_url}")
    print()
    print("STEP 2 — Dropbox will show you an access code. Copy it.")
    print()
    auth_code = prompt("Paste the access code here")

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        sys.exit(f"\nFailed to exchange code: {e}")

    refresh_token = oauth_result.refresh_token
    if not refresh_token:
        sys.exit("\nNo refresh_token returned. Make sure the app uses 'Full Dropbox' access.")

    print()
    print("=" * 60)
    print("  SUCCESS — paste these into Streamlit Cloud Secrets")
    print("=" * 60)
    print()
    print('DROPBOX_APP_KEY = "{0}"'.format(app_key))
    print('DROPBOX_APP_SECRET = "{0}"'.format(app_secret))
    print('DROPBOX_REFRESH_TOKEN = "{0}"'.format(refresh_token))
    print()
    print("(Paste these as three separate lines under your existing secrets.)")
    print()
    print("Where to paste:")
    print("  Streamlit Cloud → your app → Settings → Secrets")
    print("  https://share.streamlit.io/")
    print()


if __name__ == "__main__":
    main()
