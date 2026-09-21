"""Importación conservadora: ninguna observación se descarta silenciosamente."""

import base64
import csv
import io
import json
from dataclasses import dataclass
from zipfile import ZipFile

import numpy as np
import pandas as pd
from openpyxl import load_workbook

MAX_BYTES = 10 * 1024 * 1024
MAX_CELLS = 100_000
MAX_ROWS = 20_000


@dataclass
class Imported:
    frame: pd.DataFrame
    notes: list[str]
    sheets: list[str]


def decode_upload(contents):
    if not contents or len(contents) > MAX_BYTES * 1.4:
        raise ValueError("El archivo supera el límite de 10 MB o está vacío.")
    try:
        result = base64.b64decode(contents.split(",", 1)[1], validate=True)
    except (ValueError, IndexError) as exc:
        raise ValueError("No se pudo leer el archivo. Vuelve a seleccionarlo.") from exc
    if len(result) > MAX_BYTES:
        raise ValueError("El archivo supera el límite de 10 MB.")
    return result


def numeric_value(value, decimal="."):
    text = str(value).strip()
    if not text:
        raise ValueError("Celda vacía")
    if decimal == ",":
        if "." in text:
            raise ValueError("No se admiten separadores de miles; usa solo la coma decimal.")
        text = text.replace(",", ".")
    elif "," in text:
        raise ValueError("Revisa el separador decimal; no se admiten separadores de miles.")
    result = float(text)
    if not np.isfinite(result):
        raise ValueError("Se requiere un número finito")
    return result


def looks_numeric(value):
    try:
        return np.isfinite(float(str(value).strip().replace(",", ".")))
    except ValueError:
        return False


def read_table(raw, filename, separator="auto", header="auto", sheet=None):
    if len(raw) > MAX_BYTES:
        raise ValueError("El archivo supera los 10 MB.")
    suffix = filename.lower().rsplit(".", 1)[-1]
    notes, sheets = [], []
    if suffix == "xlsx":
        with ZipFile(io.BytesIO(raw)) as archive:
            if sum(info.file_size for info in archive.infolist()) > 50 * 1024 * 1024:
                raise ValueError("La hoja descomprimida supera 50 MB. Exporta solo la tabla necesaria.")
        # Read-only iteration bounds decompressed worksheets as well as the upload size.
        workbook = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        try:
            sheets = workbook.sheetnames
            active = sheet if sheet in sheets else sheets[0]
            worksheet = workbook[active]
            if worksheet.max_column and worksheet.max_column > 100:
                raise ValueError("Máximo 100 columnas. Elimina columnas vacías con formato.")
            rows = []
            for row in worksheet.iter_rows(values_only=True):
                if len(rows) >= MAX_ROWS + 1:
                    raise ValueError("Máximo 20.000 filas por archivo.")
                rows.append(["" if v is None else str(v) for v in row])
                if sum(map(len, rows[-1:])) * len(rows) > MAX_CELLS:
                    raise ValueError("Máximo 100.000 celdas por hoja.")
            notes.append(f"Hoja: {active}. Las fórmulas necesitan valores guardados desde Excel.")
        finally:
            workbook.close()
    elif suffix in {"csv", "tsv", "txt"}:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252")
            notes.append("Codificación Windows-1252 detectada.")
        if separator == "auto":
            try:
                separator = csv.Sniffer().sniff(text[:16000], delimiters=";,\t|").delimiter
            except csv.Error:
                separator = "\t" if suffix == "tsv" else ","
            notes.append(f"Separador detectado: {separator!r}. Confírmalo en la vista previa.")
        rows = list(csv.reader(io.StringIO(text), delimiter=separator, strict=True))
        if len(rows) > MAX_ROWS + 1 or sum(map(len, rows)) > MAX_CELLS:
            raise ValueError("Máximo 20.000 filas y 100.000 celdas.")
        widths = {len(row) for row in rows if any(str(x).strip() for x in row)}
        if len(widths) > 1:
            raise ValueError(
                "Hay filas con distinta cantidad de columnas. Revisa el separador o las comillas."
            )
    else:
        raise ValueError("Usa CSV, XLSX, TSV o TXT. Convierte archivos .xls a .xlsx.")
    blank = sum(not any(str(v).strip() for v in row) for row in rows)
    rows = [row for row in rows if any(str(v).strip() for v in row)]
    if blank:
        notes.append(f"Se omitieron {blank} filas completamente vacías; no contenían mediciones.")
    if not rows:
        raise ValueError("El archivo no contiene datos.")
    width = len(rows[0])
    if width > 100:
        raise ValueError("Máximo 100 columnas.")
    if header == "auto":
        first_numeric = any(looks_numeric(v) for v in rows[0])
        second_numeric = len(rows) > 1 and any(looks_numeric(v) for v in rows[1])
        known_headers = {
            "subgrupo",
            "subgroup",
            "medicion",
            "medición",
            "measurement",
            "defecto",
            "categoria",
            "categoría",
            "category",
            "valor",
            "frecuencia",
        }
        has_header = (not first_numeric and second_numeric) or any(
            str(v).strip().lower() in known_headers for v in rows[0]
        )
        notes.append("Encabezado inferido: " + ("sí" if has_header else "no") + ". Puedes cambiarlo arriba.")
    else:
        has_header = header == "yes"
    columns = (
        [str(v).strip() for v in rows.pop(0)] if has_header else [f"Columna {i + 1}" for i in range(width)]
    )
    if any(not v for v in columns) or len(set(columns)) != len(columns):
        raise ValueError("Los encabezados deben tener nombres únicos y no estar vacíos.")
    if not rows:
        raise ValueError("Solo hay encabezados; agrega observaciones.")
    if len(rows) > MAX_ROWS:
        raise ValueError("Máximo 20.000 filas de datos.")
    frame = pd.DataFrame(rows, columns=columns).fillna("")
    return Imported(frame, notes, sheets)


def suggest_columns(frame):
    numeric = [c for c in frame if frame[c].map(looks_numeric).all()]
    group = next((c for c in frame if c.lower() in {"subgrupo", "subgroup", "lote", "grupo", "sample"}), None)
    value = next(
        (
            c
            for c in numeric
            if c.lower() in {"measurement", "medicion", "medición", "valor", "diametro", "diámetro"}
        ),
        None,
    )
    value = value or next((c for c in numeric if c != group), None)
    measures = [c for c in numeric if c != group]
    layout = "wide" if len(measures) > 1 else "long"
    sample = frame[measures].astype(str).to_numpy().ravel() if measures else []
    decimal = "," if any("," in str(v) for v in sample) else "."
    return value, group, measures, layout, decimal


def numeric_column(frame, column, decimal):
    if column not in frame:
        raise ValueError("Selecciona una columna de medición válida.")
    values, invalid = [], []
    for i, value in enumerate(frame[column]):
        try:
            # XLSX numbers are stored with a dot regardless of display locale.
            values.append(numeric_value(value, decimal))
        except (ValueError, TypeError):
            invalid.append(str(i + 1))
    if invalid:
        raise ValueError(
            f"Columna «{column}»: valores vacíos o no numéricos en filas de datos {', '.join(invalid[:8])}. Revisa el decimal y corrige el origen."
        )
    return np.array(values, dtype=float)


def make_groups(frame, config):
    decimal = config.get("decimal", ".")
    chart = config["chart"]
    if config.get("layout") == "wide" and chart != "imr":
        columns = config.get("measures") or []
        if len(columns) < 2:
            raise ValueError("Selecciona al menos dos columnas de medición para el formato ancho.")
        matrix = np.column_stack([numeric_column(frame, c, decimal) for c in columns])
        group_col = config.get("group")
        labels = (
            frame[group_col].astype(str).tolist()
            if group_col in frame
            else [str(i + 1) for i in range(len(frame))]
        )
        if any(not label.strip() for label in labels) or len(set(labels)) != len(labels):
            raise ValueError("En formato ancho, cada fila debe tener un identificador único y no vacío.")
        return [row for row in matrix], labels
    values = numeric_column(frame, config.get("value"), decimal)
    if chart == "imr":
        return [np.array([v]) for v in values], [str(i + 1) for i in range(len(values))]
    group_col = config.get("group")
    if group_col and group_col in frame:
        ids = frame[group_col].astype(str).str.strip()
        if (ids == "").any():
            raise ValueError("Hay identificadores de subgrupo vacíos.")
        labels = list(dict.fromkeys(ids))
        return [values[(ids == label).to_numpy()] for label in labels], labels
    n = config.get("size")
    if n is None or int(n) != n or not 2 <= n <= 100:
        raise ValueError("El tamaño del subgrupo debe ser un entero entre 2 y 100.")
    n = int(n)
    if len(values) % n:
        raise ValueError(
            f"Hay {len(values)} mediciones: sobran {len(values) % n} para grupos de {n}. Completa el grupo o corrige el archivo; no se eliminarán mediciones."
        )
    return list(values.reshape(-1, n)), [str(i + 1) for i in range(len(values) // n)]


def frame_store(frame, name, notes=None):
    return {
        "columns": list(frame.columns),
        "records": frame.astype(str).to_dict("records"),
        "name": name,
        "notes": notes or [],
    }


def restore_frame(payload):
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("columns"), list)
        or not isinstance(payload.get("records"), list)
    ):
        raise ValueError("Estructura del proyecto inválida.")
    columns, rows = payload["columns"], payload["records"]
    if (
        not columns
        or not rows
        or len(columns) > 100
        or len(rows) > MAX_ROWS
        or len(columns) * len(rows) > MAX_CELLS
    ):
        raise ValueError("El proyecto está vacío o excede los límites de tamaño.")
    if not all(isinstance(c, str) and c for c in columns) or len(set(columns)) != len(columns):
        raise ValueError("Columnas inválidas en el proyecto.")
    if not all(
        isinstance(r, dict)
        and set(r) == set(columns)
        and all(isinstance(v, (str, float, int)) for v in r.values())
        for r in rows
    ):
        raise ValueError("Filas inválidas en el proyecto.")
    return pd.DataFrame(rows, columns=columns).astype(str)


def read_project(raw):
    project = json.loads(raw)
    if not isinstance(project, dict) or project.get("schema") != "statcontrol/1":
        raise ValueError("Este JSON no es un proyecto StatControl compatible.")
    restore_frame(project.get("data"))
    if not isinstance(project.get("config"), dict):
        raise ValueError("Configuración de proyecto inválida.")
    config = project["config"]
    for key, choices in {
        "chart": {"xr", "xs", "imr", "pareto"},
        "layout": {"long", "wide"},
        "decimal": {".", ","},
    }.items():
        if key in config and (not isinstance(config[key], str) or config[key] not in choices):
            raise ValueError(f"Parámetro de proyecto inválido: {key}.")
    for key in ("size", "baseline", "lsl", "usl"):
        val = config.get(key)
        if val is not None and (
            isinstance(val, bool) or not isinstance(val, (int, float)) or not np.isfinite(val)
        ):
            raise ValueError(f"Parámetro numérico inválido: {key}.")
    for key in ("value", "group", "frequency"):
        if config.get(key) is not None and not isinstance(config[key], str):
            raise ValueError(f"Columna inválida: {key}.")
    if "rules" in config and not isinstance(config["rules"], bool):
        raise ValueError("Reglas de proyecto inválidas.")
    measures = config.get("measures", [])
    if not isinstance(measures, list) or not all(isinstance(c, str) for c in measures):
        raise ValueError("Columnas de medición inválidas.")
    return project


def demo_frame():
    rng = np.random.default_rng(26)
    values = rng.normal(100, 0.22, (25, 5))
    values[20] += 0.7
    return pd.DataFrame({"subgrupo": np.repeat(np.arange(1, 26), 5), "medicion": values.ravel().round(3)})
