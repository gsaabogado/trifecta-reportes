"""
Registry of inspection report types.

Today only "Previo en Origen" is implemented (via generate_report.generate_report).
The registry exists so that adding "Inspección de Calidad" or "Auditoría de
Fábrica" later is a one-line change in the registry and a new generator
function — the rest of the app stays untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from generate_report import generate_report as _generate_previo


@dataclass(frozen=True)
class ReportType:
    key: str
    label_es: str
    label_en: str
    description_es: str
    description_en: str
    generator: Callable[..., str]
    available: bool = True

    def label(self, lang: str) -> str:
        return self.label_es if lang == "es" else self.label_en

    def description(self, lang: str) -> str:
        return self.description_es if lang == "es" else self.description_en


REPORT_TYPES: Dict[str, ReportType] = {
    "previo": ReportType(
        key="previo",
        label_es="Previo en Origen",
        label_en="Pre-Shipment Inspection",
        description_es="Inspección antes del embarque (CCI). 9 puntos de control + fotos por talla.",
        description_en="Pre-shipment inspection (CCI). 9 control points + photos per size.",
        generator=_generate_previo,
        available=True,
    ),
    "calidad": ReportType(
        key="calidad",
        label_es="Inspección de Calidad",
        label_en="Quality Inspection (AQL)",
        description_es="Inspección de calidad AQL Nivel II. (Próximamente)",
        description_en="AQL Level II quality inspection. (Coming soon)",
        generator=_generate_previo,  # placeholder
        available=False,
    ),
    "auditoria": ReportType(
        key="auditoria",
        label_es="Auditoría de Fábrica",
        label_en="Factory Audit",
        description_es="Auditoría de capacidad y procesos del proveedor. (Próximamente)",
        description_en="Supplier capacity and process audit. (Coming soon)",
        generator=_generate_previo,  # placeholder
        available=False,
    ),
}


def available_types() -> List[ReportType]:
    return [t for t in REPORT_TYPES.values() if t.available]


def all_types() -> List[ReportType]:
    return list(REPORT_TYPES.values())


def get(key: str) -> ReportType:
    return REPORT_TYPES[key]
