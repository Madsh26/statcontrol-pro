import math

import numpy as np
import pandas as pd
import pytest

from statcontrol.data import demo_frame
from statcontrol.statistics import analyze, c4, capability, signals


def config(**changes):
    values = dict(
        chart="xr",
        layout="long",
        decimal=".",
        value="medicion",
        group="subgrupo",
        size=5,
        measures=[],
        baseline=None,
        lsl=None,
        usl=None,
        rules=False,
    )
    values.update(changes)
    return values


def test_xr_hand_calculation():
    data = pd.DataFrame({"subgrupo": [1, 1, 2, 2, 3, 3], "medicion": [1, 3, 2, 4, 3, 5]})
    result = analyze(data, config())
    assert result["center"] == 3
    assert result["sigma"] == pytest.approx(2 / 1.128)
    assert result["upper"] == pytest.approx(3 + 3 * (2 / 1.128) / math.sqrt(2))
    assert result["dupper"] == pytest.approx(6.534)
    assert result["lower"] < 0  # no clipping of the Xbar lower limit


def test_xs_bias_correction():
    data = pd.DataFrame({"subgrupo": [1, 1, 1, 2, 2, 2], "medicion": [1, 2, 3, 2, 3, 4]})
    result = analyze(data, config(chart="xs"))
    assert c4(3) == pytest.approx(math.sqrt(math.pi) / 2)
    assert result["dcenter"] == 1
    assert result["sigma"] == pytest.approx(2 / math.sqrt(math.pi))
    assert result["center"] == 2.5


def test_imr_uses_only_reference_moving_ranges():
    data = pd.DataFrame({"medicion": [10, 12, 11, 50]})
    result = analyze(data, config(chart="imr", baseline=3, group=None))
    assert result["center"] == 11
    assert result["sigma"] == pytest.approx(1.5 / 1.128)
    assert result["dispersion"] == [2, 1, 39]
    assert {a["index"] for a in result["signals"]} == {3}


def test_reference_does_not_move_when_monitoring_changes():
    frame = demo_frame()
    first = analyze(frame, config(baseline=20, lsl=99, usl=101))
    frame.loc[frame.subgrupo > 20, "medicion"] += 30
    second = analyze(frame, config(baseline=20, lsl=99, usl=101))
    assert first["upper"] == second["upper"]
    assert first["capability"] == second["capability"]


def test_unequal_groups_rejected():
    with pytest.raises(ValueError, match="tamaños diferentes"):
        analyze(pd.DataFrame({"subgrupo": [1, 1, 2, 2, 2], "medicion": [1, 2, 3, 4, 5]}), config())


@pytest.mark.parametrize("bad", [0, 1, 1.5, 1000, float("nan")])
def test_invalid_baseline(bad):
    with pytest.raises((ValueError, OverflowError)):
        analyze(demo_frame(), config(baseline=bad))


def test_zero_variation_rejected():
    with pytest.raises(ValueError, match="variación interna nula"):
        analyze(pd.DataFrame({"subgrupo": [1, 1, 2, 2], "medicion": [1, 1, 2, 2]}), config())


def test_capability_uses_correct_sigma_and_one_sided():
    values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    cap = capability(values, 3.0, 1.0, 0.0, 6.0, True)
    assert cap["cp"] == cap["cpk"] == 1
    assert cap["pp"] == pytest.approx(1 / np.std(values, ddof=1))
    unilateral = capability(values, 3.0, 1.0, None, 6.0, True)
    assert unilateral["cp"] is None
    assert unilateral["cpk"] == 1
    with pytest.raises(ValueError, match="menor"):
        capability(values, 3.0, 1.0, 6.0, 0.0, True)


def test_rules_ties_and_boundary():
    labels = list(map(str, range(9)))
    found = signals([1] * 9, 0, -3, 3, labels, True)
    assert [a["rule"] for a in found] == ["Racha de 9"]
    assert signals([3, -3], 0, -3, 3, ["a", "b"]) == []
    trend = signals([1, 2, 3, 4, 5, 6], 0, -100, 100, list("abcdef"), True)
    assert trend[0]["rule"] == "Tendencia de 6"


def test_pareto_groups_categories_and_sorts_counts():
    result = analyze(
        pd.DataFrame({"defecto": ["A", "B", "A"], "cantidad": [2, 5, 1]}),
        config(chart="pareto", value="defecto", frequency="cantidad"),
    )
    assert result["labels"] == ["B", "A"]
    assert result["counts"] == [5, 3]
    assert result["total"] == 8
