"""
Trifecta brand assets for the Streamlit app.

Centralizes colors, typography, CSS injection and logo rendering so that the
look and feel stays consistent with the Word reports, Shiny apps and the
trifecta-inspections.com website.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


# --- Brand tokens (mirror www/style.css from the Shiny apps) ----------------
COLORS = {
    "navy": "#000000",        # branded "navy" — actually pure black for the logo
    "navy_light": "#1A1A1A",
    "charcoal": "#2D2A26",
    "gray_warm": "#F5F4F2",
    "gray_cool": "#D9D8D6",
    "gray_line": "#E5E4E2",
    "accent": "#0066CC",
    "success": "#1F7A4C",
    "danger": "#B23B3B",
    "white": "#FFFFFF",
}

FONT_HEADING = '"Archivo Black", "Arial Black", sans-serif'
FONT_BODY = '"Inter", "Helvetica Neue", "Arial", sans-serif'

LOGO_PATH = Path(__file__).resolve().parent.parent / "plantillas" / "logo_trifecta.png"


def _logo_base64() -> str:
    """Read the Trifecta logo as a base64 data URI for inline embedding."""
    if not LOGO_PATH.exists():
        return ""
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def inject_css() -> None:
    """Inject the Trifecta design system CSS into the current Streamlit page."""
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
      --navy: {COLORS["navy"]};
      --navy-light: {COLORS["navy_light"]};
      --charcoal: {COLORS["charcoal"]};
      --gray-warm: {COLORS["gray_warm"]};
      --gray-cool: {COLORS["gray_cool"]};
      --gray-line: {COLORS["gray_line"]};
      --accent: {COLORS["accent"]};
      --white: {COLORS["white"]};
    }}

    /* Global typography */
    html, body, [class*="css"], .stMarkdown, .stTextInput, .stRadio, .stButton,
    .stDownloadButton, .stCaption, .stMetric, .stAlert {{
      font-family: {FONT_BODY} !important;
      color: var(--charcoal);
    }}

    h1, h2, h3, h4, h5, h6 {{
      font-family: {FONT_HEADING} !important;
      color: var(--navy) !important;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    /* Hide Streamlit chrome we don't need on mobile */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{
      background: transparent;
      height: 0;
    }}

    /* Page container — give it room on mobile, cap width on desktop */
    .block-container {{
      padding-top: 1.2rem !important;
      padding-bottom: 3rem !important;
      max-width: 760px !important;
    }}

    /* Hero header */
    .trifecta-hero {{
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      padding: 1.5rem 1rem 1rem;
      border-bottom: 3px solid var(--navy);
      margin-bottom: 1.5rem;
    }}
    .trifecta-hero img {{
      max-width: 220px;
      width: 60%;
      height: auto;
      margin-bottom: 0.85rem;
    }}
    .trifecta-hero .trifecta-tagline {{
      font-family: {FONT_BODY} !important;
      font-size: 0.78rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--charcoal);
      opacity: 0.75;
    }}
    .trifecta-hero .trifecta-title {{
      font-family: {FONT_HEADING} !important;
      font-size: 1.45rem;
      letter-spacing: 0.04em;
      color: var(--navy);
      margin-top: 0.4rem;
    }}

    /* Section labels */
    .trifecta-section-label {{
      font-family: {FONT_HEADING} !important;
      font-size: 0.72rem;
      letter-spacing: 0.14em;
      color: var(--navy);
      text-transform: uppercase;
      margin: 1.2rem 0 0.4rem 0;
      padding-bottom: 0.3rem;
      border-bottom: 1px solid var(--gray-line);
    }}

    /* Cards */
    .trifecta-card {{
      background: var(--white);
      border: 1px solid var(--gray-line);
      border-radius: 14px;
      padding: 1rem 1.1rem;
      margin: 0.5rem 0 1rem 0;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }}

    /* Radios — render as pill buttons */
    .stRadio > div[role="radiogroup"] {{
      gap: 0.5rem !important;
      display: flex !important;
      flex-wrap: wrap !important;
    }}
    .stRadio div[role="radiogroup"] > label {{
      background: var(--gray-warm);
      border: 1px solid var(--gray-line);
      border-radius: 999px;
      padding: 0.5rem 1.05rem !important;
      margin: 0 !important;
      cursor: pointer;
      transition: all 0.15s ease;
      font-weight: 500;
    }}
    .stRadio div[role="radiogroup"] > label:hover {{
      border-color: var(--navy);
    }}
    /* Hide the native radio circle — the pill itself is the indicator */
    .stRadio div[role="radiogroup"] > label > div:first-child {{
      display: none !important;
    }}
    .stRadio div[role="radiogroup"] > label p {{
      color: var(--charcoal) !important;
      font-size: 0.92rem !important;
      margin: 0 !important;
    }}
    /* Selected pill */
    .stRadio div[role="radiogroup"] > label:has(input:checked) {{
      background: var(--navy) !important;
      border-color: var(--navy) !important;
    }}
    .stRadio div[role="radiogroup"] > label:has(input:checked) p {{
      color: var(--white) !important;
    }}

    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {{
      border-radius: 10px !important;
      border: 1px solid var(--gray-cool) !important;
      padding: 0.55rem 0.85rem !important;
      font-size: 0.95rem !important;
    }}
    .stTextInput > div > div > input:focus {{
      border-color: var(--navy) !important;
      box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.08) !important;
    }}

    /* Buttons */
    .stButton > button, .stDownloadButton > button {{
      background-color: var(--navy) !important;
      color: var(--white) !important;
      border: 1px solid var(--navy) !important;
      border-radius: 10px !important;
      font-family: {FONT_HEADING} !important;
      font-size: 0.85rem !important;
      letter-spacing: 0.08em !important;
      text-transform: uppercase;
      padding: 0.7rem 1.2rem !important;
      transition: all 0.18s ease;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
      background-color: var(--accent) !important;
      border-color: var(--accent) !important;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 102, 204, 0.25);
    }}
    .stButton > button:disabled {{
      background-color: var(--gray-cool) !important;
      border-color: var(--gray-cool) !important;
      color: var(--white) !important;
      box-shadow: none !important;
      transform: none !important;
    }}

    /* Metric cards */
    [data-testid="stMetric"] {{
      background: var(--gray-warm);
      border: 1px solid var(--gray-line);
      border-radius: 12px;
      padding: 0.85rem 1rem;
    }}
    [data-testid="stMetricLabel"] {{
      font-family: {FONT_BODY} !important;
      font-size: 0.7rem !important;
      font-weight: 600 !important;
      letter-spacing: 0.08em !important;
      text-transform: uppercase;
      color: var(--charcoal) !important;
      opacity: 0.75;
    }}
    [data-testid="stMetricValue"] {{
      font-family: {FONT_HEADING} !important;
      font-size: 1.6rem !important;
      color: var(--navy) !important;
    }}

    /* Alerts */
    [data-testid="stAlert"] {{
      border-radius: 12px !important;
      border-left-width: 4px !important;
    }}

    /* Progress bar */
    .stProgress > div > div > div > div {{
      background-color: var(--navy) !important;
    }}

    /* Footer */
    .trifecta-footer {{
      margin-top: 2.5rem;
      padding-top: 1rem;
      border-top: 1px solid var(--gray-line);
      text-align: center;
      font-size: 0.75rem;
      color: var(--charcoal);
      opacity: 0.65;
      letter-spacing: 0.04em;
    }}
    .trifecta-footer a {{
      color: var(--accent);
      text-decoration: none;
    }}

    /* Mobile tweaks */
    @media (max-width: 640px) {{
      .block-container {{
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
      }}
      .trifecta-hero img {{
        max-width: 180px;
      }}
      .trifecta-hero .trifecta-title {{
        font-size: 1.2rem;
      }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_hero(title: str, tagline: str = "Inspecciones · Comercio · Consultoría") -> None:
    """Render the branded hero header with logo + title."""
    logo_b64 = _logo_base64()
    img_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="Trifecta" />'
        if logo_b64
        else ""
    )
    st.markdown(
        f"""
        <div class="trifecta-hero">
          {img_html}
          <div class="trifecta-tagline">{tagline}</div>
          <div class="trifecta-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    """Render a small uppercase section label."""
    st.markdown(f'<div class="trifecta-section-label">{text}</div>', unsafe_allow_html=True)


def render_footer(version: str = "") -> None:
    """Render the page footer with brand line and optional version."""
    version_str = f" · v{version}" if version else ""
    st.markdown(
        f"""
        <div class="trifecta-footer">
          Trifecta Inspections ·
          <a href="https://trifecta-inspections.com" target="_blank">trifecta-inspections.com</a>
          {version_str}
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_icon() -> str:
    """Return a path to use as the Streamlit page icon (favicon)."""
    return str(LOGO_PATH) if LOGO_PATH.exists() else "📋"
