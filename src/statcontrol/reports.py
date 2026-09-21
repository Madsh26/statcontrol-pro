"""Exportaciones sin fórmulas ejecutables y proyectos JSON versionados."""

import io
import json
from datetime import UTC, datetime
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import __version__


def safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def result_frame(result):
    if result["chart"] == "pareto":
        return pd.DataFrame(
            {
                "categoria": result["labels"],
                "frecuencia": result["counts"],
                "porcentaje_acumulado": np.cumsum(result["counts"]) / result["total"] * 100,
            }
        )
    dispersion = result["dispersion"]
    if result["chart"] == "imr":
        dispersion = [None] + dispersion
    rules = {}
    for item in result["signals"]:
        rules.setdefault(item["index"], []).append(item["chart"] + ": " + item["rule"])
    return pd.DataFrame(
        {
            "subgrupo": result["labels"],
            "fase": [
                "Referencia" if i < result["baseline"] else "Seguimiento"
                for i in range(len(result["labels"]))
            ],
            "media": result["means"],
            "dispersion": dispersion,
            "LCI": result["lower"],
            "LC": result["center"],
            "LCS": result["upper"],
            "dispersion_LCI": result["dlower"],
            "dispersion_LC": result["dcenter"],
            "dispersion_LCS": result["dupper"],
            "senales": ["; ".join(rules.get(i, [])) for i in range(len(result["labels"]))],
        }
    )


def csv_bytes(result):
    return result_frame(result).map(safe_cell).to_csv(index=False).encode("utf-8-sig")


def excel_bytes(result):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result_frame(result).map(safe_cell).to_excel(writer, index=False, sheet_name="Resultados")
        pd.DataFrame(result["signals"]).map(safe_cell).to_excel(writer, index=False, sheet_name="Señales")
        pd.DataFrame([result.get("capability") or {}]).to_excel(writer, index=False, sheet_name="Capacidad")
        pd.DataFrame(
            {"parametro": list(result["config"]), "valor": [str(v) for v in result["config"].values()]}
        ).map(safe_cell).to_excel(writer, index=False, sheet_name="Configuración")
        for sheet in writer.book:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                sheet.column_dimensions[column[0].column_letter].width = min(
                    55, max(16, max(len(str(c.value or "")) for c in column) + 2)
                )
    return buffer.getvalue()


def project_bytes(data, config):
    return json.dumps(
        {
            "schema": "statcontrol/1",
            "app_version": __version__,
            "saved_at": datetime.now(UTC).isoformat(),
            "data": data,
            "config": config,
        },
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    ).encode("utf-8")


def mini_chart(result, secondary=False):
    ys = result["dispersion" if secondary else "means"]
    keys = ("dlower", "dcenter", "dupper") if secondary else ("lower", "center", "upper")
    limits = [result[k] for k in keys]
    low, high = min(min(ys), min(limits)), max(max(ys), max(limits))
    spread = high - low or 1
    drawing = Drawing(480, 165)

    def py(v):
        return 25 + (v - low) / spread * 110

    for value, label in zip(limits, ["LCI", "LC", "LCS"]):
        drawing.add(
            Line(
                10, py(value), 410, py(value), strokeColor=colors.HexColor("#aab8cf"), strokeDashArray=[3, 3]
            )
        )
        drawing.add(String(414, py(value) - 3, f"{label} {value:.3f}", fontSize=8))
    coords = []
    for i, value in enumerate(ys):
        coords += [10 + i / max(1, len(ys) - 1) * 400, py(value)]
    drawing.add(PolyLine(coords, strokeColor=colors.HexColor("#2864ea"), strokeWidth=1.3))
    drawing.add(String(10, 3, "Orden de observación", fontSize=9))
    return drawing


def pdf_bytes(result, name):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, title="StatControl Pro · Informe", author="StatControl Pro", topMargin=38, bottomMargin=38
    )
    styles = getSampleStyleSheet()
    story = []

    def text(value, style="BodyText"):
        paragraph = Paragraph(escape(str(value)), styles[style])
        if style.startswith("Heading") or style == "Title":
            paragraph.keepWithNext = True
            story.append(paragraph)
        else:
            story.extend([paragraph, Spacer(1, 8)])

    text("STATCONTROL PRO", "Title")
    text("Informe de control estadístico de procesos", "Heading2")
    text(f"Fuente: {name} · {datetime.now(UTC):%Y-%m-%d %H:%M} UTC · versión {__version__}")
    text(f"Tipo: {result['chart'].upper()} · Observaciones/frecuencias: {result['total']}")
    if result["chart"] != "pareto":
        text(
            f"Referencia: primeros {result['baseline']} puntos · n = {result['n']} · sigma interna = {result['sigma']:.5f}"
        )
        text(f"Media: {result['center']:.5f} · LCI: {result['lower']:.5f} · LCS: {result['upper']:.5f}")
        text("Gráfico de medias / individuales", "Heading3")
        story.append(mini_chart(result))
        text(result["dispersion_name"], "Heading3")
        story.append(mini_chart(result, True))
        cap = result.get("capability")
        if cap:
            text("Capacidad de la referencia", "Heading2")
            if cap.get("unavailable"):
                text(cap["unavailable"])
            else:
                text(
                    " · ".join(
                        f"{k.upper()}: {cap[k]:.3f}" for k in ("cp", "cpk", "pp", "ppk") if cap[k] is not None
                    )
                )
                text(
                    f"Fuera de especificación observado: {cap['observed_pct']:.2f}% · PPM bajo modelo normal: {cap['normal_ppm']:.1f}"
                )
                p_label = f"{cap['normality_p']:.4f}" if cap["normality_p"] is not None else "No calculado"
                text(f"Shapiro-Wilk p: {p_label} · Referencia sin señales: {'Sí' if cap['stable'] else 'No'}")
    else:
        table = Table(
            [["Categoría", "Frecuencia"]]
            + [
                [Paragraph(escape(str(a)), styles["BodyText"]), str(b)]
                for a, b in zip(result["labels"], result["counts"])
            ],
            colWidths=[340, 100],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0ff")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(table)
    text("Interpretación y señales", "Heading2")
    text(f"Se detectaron {len(result['signals'])} eventos de señal; pueden coincidir en un mismo punto.")
    for warning in result["warnings"]:
        text(warning)
    for alert in result["signals"][:100]:
        text(f"{alert['chart']} · {alert['point']}: {alert['detail']}")
    if len(result["signals"]) > 100:
        text("Se muestran los primeros 100 eventos; consulta Excel para la lista completa.")
    text("Configuración reproducible", "Heading2")
    for key, value in result["config"].items():
        text(f"{key}: {value}")
    text(
        "Método: límites Shewhart de 3 sigma; Nelson 1 y opcionalmente 2–3 en medias/individuales. Capacidad normal calculada sobre la referencia. Consulta docs/METODOLOGIA.md para fórmulas, supuestos y alcance."
    )

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#78849a"))
        canvas.drawString(72, 22, "StatControl Pro | Informe de análisis")
        canvas.drawRightString(document.pagesize[0] - 72, 22, f"Página {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
