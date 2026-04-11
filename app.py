"""
Trifecta CCI Report Generator — Streamlit Cloud entry point.

Generates branded inspection reports from a Google Drive or Dropbox folder
link, accessible from any device.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

# Make local src/ importable on Streamlit Cloud
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from branding import inject_css, page_icon, render_footer, render_hero, section_label
from config import APP_VERSION, load_settings
from report_types import REPORT_TYPES, available_types

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Trifecta · Generador de Reportes",
    page_icon=page_icon(),
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_css()

settings = load_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def t(es: str, en: str, lang: str) -> str:
    return es if lang == "es" else en


def folder_summary(folder_path: str, lang: str) -> None:
    """Show a metric strip with the contents of an inspection folder."""
    folder = Path(folder_path)
    photos_dir = folder / "2.Photos"
    products_dir = photos_dir / "1.Products"
    container_dir = photos_dir / "2.Container"

    cols = st.columns(3)
    sizes_count = 0
    photos_count = 0
    container_count = 0

    if products_dir.exists():
        sizes = [d for d in products_dir.iterdir() if d.is_dir()]
        sizes_count = len(sizes)
        photos_count = sum(len(list(d.iterdir())) for d in sizes)
    if container_dir.exists():
        container_count = len(list(container_dir.iterdir()))

    cols[0].metric(t("Tallas", "Sizes", lang), sizes_count)
    cols[1].metric(t("Fotos producto", "Product photos", lang), photos_count)
    cols[2].metric(t("Fotos contenedor", "Container photos", lang), container_count)


def run_generation(local_folder: str, lang: str, type_key: str) -> None:
    """Generate the report and offer the download button."""
    report_type = REPORT_TYPES[type_key]
    with st.spinner(t("Generando reporte...", "Generating report...", lang)):
        try:
            output_path = Path(tempfile.mkdtemp()) / f"Reporte_{report_type.key.title()}_Trifecta.docx"
            report_type.generator(local_folder, str(output_path), lang=lang)

            with open(output_path, "rb") as f:
                docx_bytes = f.read()

            size_mb = len(docx_bytes) / 1024 / 1024
            st.success(
                t(
                    f"Reporte generado ({size_mb:.1f} MB)",
                    f"Report ready ({size_mb:.1f} MB)",
                    lang,
                )
            )
            st.download_button(
                label=t("Descargar reporte (.docx)", "Download report (.docx)", lang),
                data=docx_bytes,
                file_name=output_path.name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as e:
            st.error(t(f"Error generando el reporte: {e}", f"Error generating report: {e}", lang))
            with st.expander(t("Detalles técnicos", "Technical details", lang)):
                st.exception(e)


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
render_hero(
    title="Generador de Reportes",
    tagline="Inspecciones · Comercio · Consultoría",
)

# ---------------------------------------------------------------------------
# Step 1 — Language + report type
# ---------------------------------------------------------------------------
section_label("Idioma / Language")
lang_label = st.radio(
    label="lang",
    options=["Español", "English"],
    horizontal=True,
    label_visibility="collapsed",
)
lang = "es" if lang_label == "Español" else "en"

types = available_types()
if len(types) > 1:
    section_label(t("Tipo de reporte", "Report type", lang))
    type_labels = [rt.label(lang) for rt in types]
    selected_label = st.radio(
        label="type",
        options=type_labels,
        horizontal=True,
        label_visibility="collapsed",
    )
    type_key = types[type_labels.index(selected_label)].key
else:
    type_key = types[0].key
    st.caption(t(f"Tipo: {types[0].label('es')}", f"Type: {types[0].label('en')}", lang))

# ---------------------------------------------------------------------------
# Step 2 — Source selection
# ---------------------------------------------------------------------------
section_label(t("Fuente de las fotos", "Photo source", lang))

source_options = []
if settings.has_gdrive:
    source_options.append("gdrive")
if settings.has_dropbox:
    source_options.append("dropbox")
if settings.allow_local_path:
    source_options.append("local")

if not source_options:
    st.error(
        t(
            "Ninguna fuente está configurada. Configure GDRIVE_SERVICE_ACCOUNT "
            "o DROPBOX_ACCESS_TOKEN en los secrets de Streamlit.",
            "No source is configured. Set GDRIVE_SERVICE_ACCOUNT or "
            "DROPBOX_ACCESS_TOKEN in Streamlit secrets.",
            lang,
        )
    )
    st.stop()

source_label_map = {
    "gdrive": t("Google Drive", "Google Drive", lang),
    "dropbox": t("Dropbox", "Dropbox", lang),
    "local": t("Carpeta local", "Local folder", lang),
}
source_choice = st.radio(
    label="source",
    options=source_options,
    format_func=lambda key: source_label_map[key],
    horizontal=True,
    label_visibility="collapsed",
)

# ---------------------------------------------------------------------------
# Step 3 — Input + run
# ---------------------------------------------------------------------------
section_label(t("Carpeta de inspección", "Inspection folder", lang))

if source_choice == "gdrive":
    from gdrive_download import download_gdrive_folder, extract_folder_id
    from google.oauth2 import service_account

    url = st.text_input(
        t("Link de Google Drive", "Google Drive link", lang),
        placeholder="https://drive.google.com/drive/folders/...",
    )
    if url:
        try:
            folder_id = extract_folder_id(url)
            st.caption(f"Folder ID: `{folder_id[:14]}...`")
        except ValueError as e:
            st.error(str(e))
            st.stop()

        if st.button(
            t("Generar reporte", "Generate report", lang),
            type="primary",
            use_container_width=True,
        ):
            progress_bar = st.progress(0, text=t("Conectando con Google Drive...", "Connecting to Google Drive...", lang))
            try:
                creds = service_account.Credentials.from_service_account_info(
                    settings.gdrive_sa_info(),
                    scopes=["https://www.googleapis.com/auth/drive.readonly"],
                )

                def cb(current, total, filename):
                    progress_bar.progress(
                        current / total,
                        text=t(
                            f"Descargando {current}/{total}: {filename}",
                            f"Downloading {current}/{total}: {filename}",
                            lang,
                        ),
                    )

                local_folder = download_gdrive_folder(url, creds=creds, progress_callback=cb)
                progress_bar.empty()
            except Exception as e:
                progress_bar.empty()
                st.error(t(f"Error descargando: {e}", f"Download error: {e}", lang))
                st.stop()

            folder_summary(local_folder, lang)
            run_generation(local_folder, lang, type_key)

elif source_choice == "dropbox":
    from dropbox_download import download_dropbox_folder, is_dropbox_url

    url = st.text_input(
        t("Link de Dropbox", "Dropbox link", lang),
        placeholder="https://www.dropbox.com/scl/fo/...",
    )
    if url:
        if not is_dropbox_url(url):
            st.error(t("No parece un link de Dropbox válido.", "That doesn't look like a Dropbox link.", lang))
            st.stop()

        if st.button(
            t("Generar reporte", "Generate report", lang),
            type="primary",
            use_container_width=True,
        ):
            progress_bar = st.progress(0, text=t("Conectando con Dropbox...", "Connecting to Dropbox...", lang))
            try:
                def cb(current, total, filename):
                    progress_bar.progress(
                        current / total,
                        text=t(
                            f"Descargando {current}/{total}: {filename}",
                            f"Downloading {current}/{total}: {filename}",
                            lang,
                        ),
                    )

                local_folder = download_dropbox_folder(
                    url,
                    access_token=settings.dropbox_access_token,
                    refresh_token=settings.dropbox_refresh_token,
                    app_key=settings.dropbox_app_key,
                    app_secret=settings.dropbox_app_secret,
                    progress_callback=cb,
                )
                progress_bar.empty()
            except Exception as e:
                progress_bar.empty()
                st.error(t(f"Error descargando: {e}", f"Download error: {e}", lang))
                st.stop()

            folder_summary(local_folder, lang)
            run_generation(local_folder, lang, type_key)

elif source_choice == "local":
    folder_path = st.text_input(
        t("Ruta de la carpeta", "Folder path", lang),
        placeholder="/Users/.../CCI-26KOV-0001 (KL25KOV063)",
    )
    if folder_path:
        if not Path(folder_path).exists():
            st.error(t("Carpeta no encontrada.", "Folder not found.", lang))
        else:
            folder_summary(folder_path, lang)
            if st.button(
                t("Generar reporte", "Generate report", lang),
                type="primary",
                use_container_width=True,
            ):
                run_generation(folder_path, lang, type_key)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
render_footer(version=APP_VERSION)
