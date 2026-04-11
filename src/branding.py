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


# ---------------------------------------------------------------------------
# Bilingual instructions panel
# ---------------------------------------------------------------------------
_INSTRUCTIONS = {
    "es": {
        "title": "Cómo usar la app",
        "intro": (
            "Esta app genera reportes de previo en origen (CCI) automáticamente "
            "a partir de una carpeta de fotos de la inspección."
        ),
        "structure_label": "Estructura de carpeta requerida",
        "structure_intro": (
            "Su carpeta de inspección **debe** tener esta estructura. "
            "Las marcadas como obligatorias son necesarias para que el reporte se genere; "
            "las opcionales se incluyen si existen."
        ),
        "tree": """CCI-XXXXX-XXXX/
├── 2.Photos/                    ← OBLIGATORIO
│   ├── 1.Products/              ← OBLIGATORIO
│   │   ├── S/                   ← Subcarpeta por talla con fotos
│   │   ├── M/                   ← Mínimo una talla con fotos
│   │   ├── L/
│   │   └── XL/
│   ├── 2.Container/             ← Opcional (recomendado)
│   └── Other/                   ← Opcional
└── 3.Documents/                 ← Opcional
    └── 1.Acknowledgement/       ← Acuses firmados""",
        "steps_label": "Pasos para generar un reporte",
        "steps": [
            "Suba la carpeta de inspección a **Dropbox** o **Google Drive**.",
            "Comparta la carpeta como **«Cualquier persona con el link puede ver»**.",
            "Copie el link de la carpeta compartida.",
            "Seleccione el idioma del reporte (Español o English).",
            "Seleccione la fuente (Dropbox o Google Drive) y pegue el link.",
            "Verifique que la estructura de carpetas sea correcta (la app le avisará si falta algo).",
            "Click en **«Generar reporte»** y espere mientras se descargan las fotos.",
            "Descargue el archivo `.docx` y revíselo antes de enviarlo al cliente.",
        ],
        "notes_label": "Notas",
        "notes": [
            "Las fotos se **comprimen automáticamente** a 800×600 JPG para acelerar la descarga.",
            "Los nombres de las tallas (S, M, L, XL...) se usan tal cual aparecen en la carpeta.",
            "Las carpetas ocultas (`.git`, `.claude`, etc.) se ignoran.",
            "Si comparte desde Dropbox, asegúrese que el link sea **público** (no «solo para personas específicas»).",
            "Si comparte desde Google Drive, comparta la carpeta con el correo de servicio: `trifecta-reportes@trifecta-reportes.iam.gserviceaccount.com`",
        ],
    },
    "en": {
        "title": "How to use the app",
        "intro": (
            "This app automatically generates pre-shipment inspection (CCI) reports "
            "from a folder of inspection photos."
        ),
        "structure_label": "Required folder structure",
        "structure_intro": (
            "Your inspection folder **must** match this layout. "
            "Items marked required are necessary for the report to generate; "
            "optional items are included if present."
        ),
        "tree": """CCI-XXXXX-XXXX/
├── 2.Photos/                    ← REQUIRED
│   ├── 1.Products/              ← REQUIRED
│   │   ├── S/                   ← One subfolder per size, with photos
│   │   ├── M/                   ← At least one size with photos
│   │   ├── L/
│   │   └── XL/
│   ├── 2.Container/             ← Optional (recommended)
│   └── Other/                   ← Optional
└── 3.Documents/                 ← Optional
    └── 1.Acknowledgement/       ← Signed acknowledgments""",
        "steps_label": "Steps to generate a report",
        "steps": [
            "Upload the inspection folder to **Dropbox** or **Google Drive**.",
            "Share the folder as **\"Anyone with the link can view\"**.",
            "Copy the shared folder link.",
            "Select the report language (Español or English).",
            "Select the source (Dropbox or Google Drive) and paste the link.",
            "Check the folder structure validation (the app will warn you if anything is missing).",
            "Click **\"Generate report\"** and wait while the photos download.",
            "Download the `.docx` and review it before sending to the client.",
        ],
        "notes_label": "Notes",
        "notes": [
            "Photos are **automatically compressed** to 800×600 JPG to speed up downloads.",
            "Size names (S, M, L, XL...) are used exactly as they appear in the folder.",
            "Hidden folders (`.git`, `.claude`, etc.) are ignored.",
            "If sharing from Dropbox, make sure the link is **public** (not \"only specific people\").",
            "If sharing from Google Drive, share the folder with the service account email: `trifecta-reportes@trifecta-reportes.iam.gserviceaccount.com`",
        ],
    },
}


def render_instructions(lang: str = "es") -> None:
    """Render the bilingual 'how to use' panel as a collapsible expander."""
    txt = _INSTRUCTIONS.get(lang, _INSTRUCTIONS["es"])
    with st.expander(f"📖 {txt['title']}", expanded=False):
        st.markdown(txt["intro"])
        st.markdown(f"**{txt['structure_label']}**")
        st.markdown(txt["structure_intro"])
        st.code(txt["tree"], language="text")
        st.markdown(f"**{txt['steps_label']}**")
        for i, step in enumerate(txt["steps"], 1):
            st.markdown(f"{i}. {step}")
        st.markdown(f"**{txt['notes_label']}**")
        for note in txt["notes"]:
            st.markdown(f"- {note}")
