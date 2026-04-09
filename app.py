"""
Trifecta CCI Report Generator — Streamlit Cloud App
Generates inspection reports from Google Drive or Dropbox folder links.
"""

import streamlit as st
import tempfile
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))
from generate_report import generate_report
from gdrive_download import download_gdrive_folder, extract_folder_id

# --- Google Drive auth from Streamlit secrets ---
def get_gdrive_service():
    """Build Google Drive service from Streamlit secrets (service account)."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    # Load service account credentials from Streamlit secrets
    sa_info = json.loads(st.secrets["GDRIVE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service


def download_gdrive_with_secrets(url, progress_bar=None):
    """Download a Google Drive folder using service account from secrets."""
    from gdrive_download import download_gdrive_folder

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    sa_info = json.loads(st.secrets["GDRIVE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(sa_info, scopes=SCOPES)

    def progress_callback(current, total, filename):
        if progress_bar:
            progress_bar.progress(current / total, text=f"Descargando {current}/{total}: {filename}")

    return download_gdrive_folder(url, creds=creds, progress_callback=progress_callback)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Trifecta — Generador de Reportes CCI",
    page_icon="📋",
    layout="centered",
)

st.title("Trifecta CCI Report Generator")
st.markdown("Genera un reporte de inspección de previo en origen a partir de una carpeta de fotos.")
st.divider()

# Language
lang = st.radio("Idioma del reporte:", ["Español", "English"], horizontal=True)
lang_code = "es" if lang == "Español" else "en"

# Input mode
input_mode = st.radio(
    "Fuente de datos:",
    ["Google Drive link", "Dropbox link (próximamente)", "Ruta local (desarrollo)"],
    horizontal=True,
)

if input_mode == "Google Drive link":
    url = st.text_input(
        "Link de Google Drive",
        placeholder="https://drive.google.com/drive/folders/...",
        help="Pega el link de la carpeta compartida en Google Drive.",
    )

    if url:
        try:
            folder_id = extract_folder_id(url)
            st.caption(f"Folder ID: `{folder_id}`")
        except ValueError as e:
            st.error(str(e))
            st.stop()

        if st.button("Generar Reporte", type="primary", use_container_width=True):
            progress_bar = st.progress(0, text="Descargando carpeta de Google Drive...")
            try:
                local_folder = download_gdrive_with_secrets(url, progress_bar=progress_bar)
                progress_bar.empty()
            except Exception as e:
                progress_bar.empty()
                st.error(f"Error descargando de Google Drive: {e}")
                st.stop()

            # Show summary
            photos_dir = Path(local_folder) / "2.Photos"
            products_dir = photos_dir / "1.Products"
            container_dir = photos_dir / "2.Container"

            if products_dir.exists():
                sizes = [d.name for d in products_dir.iterdir() if d.is_dir()]
                total_photos = sum(
                    len(list(d.iterdir())) for d in products_dir.iterdir() if d.is_dir()
                )
                col1, col2, col3 = st.columns(3)
                col1.metric("Tallas", len(sizes))
                col2.metric("Fotos producto", total_photos)
                if container_dir.exists():
                    col3.metric("Fotos contenedor", len(list(container_dir.iterdir())))

            with st.spinner("Generando reporte..."):
                try:
                    output_path = Path(tempfile.mkdtemp()) / "Reporte_CCI_Trifecta.docx"
                    generate_report(local_folder, str(output_path), lang=lang_code)

                    with open(output_path, "rb") as f:
                        docx_bytes = f.read()

                    st.success(f"Reporte generado ({len(docx_bytes) / 1024 / 1024:.1f} MB)")
                    st.download_button(
                        label="Descargar Reporte (.docx)",
                        data=docx_bytes,
                        file_name="Reporte_CCI_Trifecta.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Error generando reporte: {e}")
                    st.exception(e)

elif "Ruta local" in input_mode:
    folder_path = st.text_input(
        "Ruta de la carpeta",
        placeholder="/Users/.../CCI-26KOV-0001 (KL25KOV063)",
    )

    if folder_path and Path(folder_path).exists():
        if st.button("Generar Reporte", type="primary", use_container_width=True):
            with st.spinner("Generando reporte..."):
                try:
                    output_path = Path(tempfile.mkdtemp()) / "Reporte_CCI_Trifecta.docx"
                    generate_report(folder_path, str(output_path), lang=lang_code)

                    with open(output_path, "rb") as f:
                        docx_bytes = f.read()

                    st.success(f"Reporte generado ({len(docx_bytes) / 1024 / 1024:.1f} MB)")
                    st.download_button(
                        label="Descargar Reporte (.docx)",
                        data=docx_bytes,
                        file_name="Reporte_CCI_Trifecta.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Error generando reporte: {e}")
                    st.exception(e)
    elif folder_path:
        st.error("Carpeta no encontrada.")

else:
    st.info("Soporte para Dropbox será agregado próximamente.")

# Footer
st.divider()
st.caption("Trifecta Inspections | trifecta-inspections.com")
