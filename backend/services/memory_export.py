"""
Export de la memoria de un proyecto (workspace) — Capa 1B.

Genera un documento descargable con los items de memoria del proyecto para
llevar a una reunión: PDF (profesional, reportlab) o CSV (abre en Excel).

A diferencia de document_service.py (atado al modelo Project / pagos /
hitos), esto es self-contained y opera sobre la lista de items de memoria
ya cargada por el caller.

Cada item es un dict con: key, value, confidence, source, updated_at.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_SOURCE_LABEL = {
    "manual": "Manual",
    "auto-silent": "Auto",
    "auto-confirmed": "Auto (confirmado)",
}
_CONF_LABEL = {"high": "Alta", "medium": "Media", "low": "Baja"}


def _esc(v: Any) -> str:
    return "" if v is None else str(v)


def _pdf(v: Any) -> str:
    """Escapa el texto para el mini-markup tipo XML de reportlab Paragraph.

    Sin esto, un value con '<' o '&' rompe el render (lanza excepción → 500)
    o inyecta formato/tags en el PDF. Escapa &, < y > a entidades.
    """
    return _xml_escape(_esc(v))


# CSV/formula injection: un campo que arranca con uno de estos caracteres puede
# ejecutar fórmulas o DDE al abrirse en Excel/LibreOffice/Sheets. El export de
# memoria está pensado para compartirse ("llevar a una reunión"), así que el
# archivo cruza una frontera de confianza: lo abre alguien distinto del que lo
# generó. Prefijamos con apóstrofo para forzar interpretación como texto literal.
_CSV_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(v: Any) -> str:
    s = _esc(v)
    if s and s[0] in _CSV_FORMULA_TRIGGERS:
        return "'" + s
    return s


def render_memory_pdf(project_name: str, items: list[dict[str, Any]]) -> bytes:
    """Genera el PDF de memoria del proyecto."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Memoria — {project_name}",
    )
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h1.textColor = colors.HexColor("#0f172a")
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14)
    cell = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=9, leading=12)
    cell_b = ParagraphStyle(
        "cellb", parent=cell, fontName="Helvetica-Bold", textColor=colors.HexColor("#334155")
    )

    story: list[Any] = []
    story.append(Paragraph(f"Memoria del proyecto: {_pdf(project_name)}", h1))
    story.append(
        Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} — RE Expert",
            body,
        )
    )
    story.append(Spacer(1, 0.6 * cm))

    if not items:
        story.append(
            Paragraph("Este proyecto todavía no tiene memoria guardada.", body)
        )
        doc.build(story)
        return buf.getvalue()

    rows: list[list[Any]] = [
        [
            Paragraph("Dato", cell_b),
            Paragraph("Valor", cell_b),
            Paragraph("Confianza", cell_b),
            Paragraph("Origen", cell_b),
        ]
    ]
    for it in items:
        key = _pdf(it.get("key")).replace("_", " ")
        rows.append(
            [
                Paragraph(key, cell),
                Paragraph(_pdf(it.get("value")), cell),
                Paragraph(_CONF_LABEL.get(it.get("confidence"), "—"), cell),
                Paragraph(_SOURCE_LABEL.get(it.get("source"), "—"), cell),
            ]
        )
    t = Table(rows, colWidths=[4.2 * cm, 8.3 * cm, 1.8 * cm, 2.2 * cm], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            f"{len(items)} dato(s) en memoria. Documento generado automáticamente.",
            body,
        )
    )
    doc.build(story)
    return buf.getvalue()


def render_memory_csv(project_name: str, items: list[dict[str, Any]]) -> bytes:
    """Genera el CSV (UTF-8 con BOM para que Excel muestre acentos)."""
    sio = io.StringIO()
    w = csv.writer(sio)
    w.writerow(["Proyecto", _csv_safe(project_name)])
    w.writerow(["Generado", datetime.now().strftime("%d/%m/%Y %H:%M")])
    w.writerow([])
    w.writerow(["Dato", "Valor", "Confianza", "Origen"])
    for it in items:
        w.writerow(
            [
                _csv_safe(it.get("key")),
                _csv_safe(it.get("value")),
                _CONF_LABEL.get(it.get("confidence"), ""),
                _SOURCE_LABEL.get(it.get("source"), ""),
            ]
        )
    # BOM para Excel.
    return ("\ufeff" + sio.getvalue()).encode("utf-8")
