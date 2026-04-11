"""
Validate that an inspection folder has the layout that generate_report.py needs.

The report generator hard-requires:
  <folder>/2.Photos/
  <folder>/2.Photos/1.Products/<size>/   (at least one subfolder with images)

It uses (but tolerates being missing):
  <folder>/2.Photos/2.Container/
  <folder>/2.Photos/Other/
  <folder>/3.Documents/

This module raises no exceptions — it returns a `FolderValidation` object
with errors (blocking) and warnings (advisory) so the UI can render them
nicely instead of letting the user click Generate and see a stack trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
DOC_EXTS = {".doc", ".docx", ".pdf", ".xls", ".xlsx", ".txt"}


@dataclass
class FolderValidation:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    sizes_count: int = 0
    products_count: int = 0
    container_count: int = 0
    docs_count: int = 0

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def _count_images(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(
        1 for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    )


def _count_files_recursive(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.rglob("*") if f.is_file())


# --- Bilingual messages ----------------------------------------------------
_MSG = {
    "es": {
        "no_folder": "La carpeta no existe.",
        "no_photos": "Falta la carpeta obligatoria '2.Photos/'.",
        "no_products": "Falta la carpeta obligatoria '2.Photos/1.Products/'. Sin esta carpeta no se pueden generar las páginas de productos.",
        "empty_products": "'2.Photos/1.Products/' no contiene ninguna subcarpeta. Debe haber al menos una subcarpeta por talla (por ejemplo S, M, L, XL).",
        "no_product_images": "Las subcarpetas de tallas existen pero no contienen imágenes.",
        "no_container": "Falta '2.Photos/2.Container/'. La sección de contenedor del reporte estará vacía.",
        "empty_container": "'2.Photos/2.Container/' no contiene fotos. La sección de contenedor del reporte estará vacía.",
        "no_docs": "Falta '3.Documents/'. La página de acuse no incluirá documentos.",
    },
    "en": {
        "no_folder": "Folder does not exist.",
        "no_photos": "Missing required '2.Photos/' folder.",
        "no_products": "Missing required '2.Photos/1.Products/' folder. Without this no product pages can be generated.",
        "empty_products": "'2.Photos/1.Products/' has no subfolders. There must be at least one size subfolder (e.g. S, M, L, XL).",
        "no_product_images": "Size subfolders exist but contain no images.",
        "no_container": "Missing '2.Photos/2.Container/'. The container section of the report will be empty.",
        "empty_container": "'2.Photos/2.Container/' has no photos. The container section of the report will be empty.",
        "no_docs": "Missing '3.Documents/'. The acknowledgment page will not include any documents.",
    },
}


def validate_folder(folder_path: Union[str, Path], lang: str = "es") -> FolderValidation:
    """Inspect `folder_path` and return a FolderValidation report.

    Errors are blocking; warnings are advisory.
    """
    msg = _MSG.get(lang, _MSG["es"])
    folder = Path(folder_path)
    v = FolderValidation()

    if not folder.exists():
        v.errors.append(msg["no_folder"])
        return v

    photos = folder / "2.Photos"
    products = photos / "1.Products"
    container = photos / "2.Container"
    docs = folder / "3.Documents"

    # 2.Photos is hard-required
    if not photos.exists():
        v.errors.append(msg["no_photos"])
        return v  # nothing else to check

    # 1.Products is hard-required and must contain at least one non-empty size folder
    if not products.exists():
        v.errors.append(msg["no_products"])
    else:
        size_dirs = [d for d in products.iterdir() if d.is_dir()]
        v.sizes_count = len(size_dirs)
        v.products_count = sum(_count_images(d) for d in size_dirs)
        if v.sizes_count == 0:
            v.errors.append(msg["empty_products"])
        elif v.products_count == 0:
            v.errors.append(msg["no_product_images"])

    # 2.Container is optional but advised
    if not container.exists():
        v.warnings.append(msg["no_container"])
    else:
        v.container_count = _count_images(container)
        if v.container_count == 0:
            v.warnings.append(msg["empty_container"])

    # 3.Documents is optional but advised
    if not docs.exists():
        v.warnings.append(msg["no_docs"])
    else:
        v.docs_count = _count_files_recursive(docs)

    return v
