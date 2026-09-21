import io

import pandas as pd
import pytest
from openpyxl import Workbook

from statcontrol.data import demo_frame, frame_store, make_groups, read_project, read_table, suggest_columns
from statcontrol.reports import project_bytes


def test_no_header_preserves_first_measurement():
    imported = read_table(b"100.2,99.8,100.5\n100.4,100.0,99.8\n", "sample.csv")
    assert imported.frame.shape == (2, 3)
    assert imported.frame.iloc[0, 0] == "100.2"
    assert suggest_columns(imported.frame)[3] == "wide"


def test_decimal_comma_semicolon():
    frame = read_table(b"subgrupo;medicion\n1;100,2\n1;100,1\n2;99,9\n2;100,3", "test.csv").frame
    value, group, _, _, decimal = suggest_columns(frame)
    assert (value, group, decimal) == ("medicion", "subgrupo", ",")
    groups, labels = make_groups(
        frame, dict(chart="xr", layout="long", value=value, group=group, decimal=decimal)
    )
    assert groups[0].tolist() == [100.2, 100.1]
    assert labels == ["1", "2"]


def test_tab_paste():
    frame = read_table(b"medicion\n10\n12\n11", "x.tsv").frame
    assert frame.shape == (3, 1)


def test_blank_rows_reported_but_partial_rows_not_dropped():
    imported = read_table(b"a,b\n1,2\n\n3,\n", "x.csv", separator=",")
    assert imported.frame.shape == (2, 2)
    assert any("vacías" in note for note in imported.notes)
    with pytest.raises(ValueError, match="filas de datos 2"):
        make_groups(imported.frame, dict(chart="xr", layout="wide", measures=["a", "b"], decimal="."))


def test_missing_cells_and_remainders_are_errors():
    config = dict(chart="xr", layout="long", value="x", group=None, size=2, decimal=".")
    with pytest.raises(ValueError, match="sobran"):
        make_groups(pd.DataFrame({"x": [1, 2, 3]}), config)
    with pytest.raises(ValueError, match="no numéricos"):
        make_groups(pd.DataFrame({"x": [1, "", 3, 4]}), config)


def test_excel_sheet_selection_and_numeric_first_row():
    book = Workbook()
    book.active.title = "Primera"
    book.active.append([1, 2])
    book.active.append([3, 4])
    other = book.create_sheet("Otra")
    other.append(["medicion"])
    other.append([5])
    other.append([6])
    buffer = io.BytesIO()
    book.save(buffer)
    imported = read_table(buffer.getvalue(), "data.xlsx", sheet="Otra")
    assert imported.sheets == ["Primera", "Otra"]
    assert imported.frame.medicion.tolist() == ["5", "6"]
    assert read_table(buffer.getvalue(), "data.xlsx").frame.shape == (2, 2)


def test_duplicate_headers_and_ragged_rows():
    with pytest.raises(ValueError, match="únicos"):
        read_table(b"a,a\n1,2", "x.csv", header="yes")
    with pytest.raises(ValueError, match="distinta cantidad"):
        read_table(b"a,b\n1,2,3", "x.csv", separator=",")


def test_order_preserved():
    groups, labels = make_groups(
        pd.DataFrame({"g": ["B", "B", "A", "A"], "x": [1, 2, 3, 4]}),
        dict(chart="xr", layout="long", group="g", value="x", decimal="."),
    )
    assert labels == ["B", "A"]
    assert groups[0].tolist() == [1, 2]


def test_project_roundtrip_and_schema_validation():
    data = frame_store(demo_frame(), "example")
    restored = read_project(project_bytes(data, {"chart": "xr"}))
    assert restored["data"] == data
    with pytest.raises(ValueError):
        read_project(b'{"schema":"other"}')


def test_pareto_header_is_detected_without_numeric_data():
    imported = read_table(b"defecto\nRayado\nMancha\nRayado", "defectos.csv")
    assert imported.frame.columns.tolist() == ["defecto"]
    assert len(imported.frame) == 3


def test_invalid_project_configuration_rejected_before_ui():
    data = frame_store(demo_frame(), "demo")
    with pytest.raises(ValueError, match="Parámetro"):
        read_project(project_bytes(data, {"chart": ["xr"]}))


def test_wide_template_suggestion_excludes_id():
    frame = pd.DataFrame({"subgrupo": [1, 2], "m1": [2, 3], "m2": [4, 5]})
    _, group, measures, arrangement, _ = suggest_columns(frame)
    assert (group, measures, arrangement) == ("subgrupo", ["m1", "m2"], "wide")
