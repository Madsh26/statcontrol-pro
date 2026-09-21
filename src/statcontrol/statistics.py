"""Shewhart, reglas de Nelson 1–3 y capacidad normal. Sin dependencias de UI."""

import math

import numpy as np
from scipy.special import gammaln
from scipy.stats import norm, shapiro

from .data import make_groups, numeric_column

# qcc / tablas Shewhart: constantes redondeadas a 3 decimales.
D2 = dict(
    enumerate(
        [
            1.128,
            1.693,
            2.059,
            2.326,
            2.534,
            2.704,
            2.847,
            2.970,
            3.078,
            3.173,
            3.258,
            3.336,
            3.407,
            3.472,
            3.532,
            3.588,
            3.640,
            3.689,
            3.735,
            3.778,
            3.819,
            3.858,
            3.895,
            3.931,
        ],
        2,
    )
)
D3 = dict(
    enumerate(
        [
            0,
            0,
            0,
            0,
            0,
            0.076,
            0.136,
            0.184,
            0.223,
            0.256,
            0.283,
            0.307,
            0.328,
            0.347,
            0.363,
            0.378,
            0.391,
            0.403,
            0.415,
            0.425,
            0.434,
            0.443,
            0.451,
            0.459,
        ],
        2,
    )
)
D4 = dict(
    enumerate(
        [
            3.267,
            2.574,
            2.282,
            2.114,
            2.004,
            1.924,
            1.864,
            1.816,
            1.777,
            1.744,
            1.717,
            1.693,
            1.672,
            1.653,
            1.637,
            1.622,
            1.608,
            1.597,
            1.585,
            1.575,
            1.566,
            1.557,
            1.548,
            1.541,
        ],
        2,
    )
)


def c4(n):
    return float(math.sqrt(2 / (n - 1)) * math.exp(gammaln(n / 2) - gammaln((n - 1) / 2)))


def signals(values, center, lower, upper, labels, extended=False, chart="Media"):
    y = np.array(values)
    results = []
    for i in np.flatnonzero((y < lower) | (y > upper)):
        results.append(
            {
                "index": int(i),
                "point": labels[i],
                "chart": chart,
                "rule": "Fuera de límites",
                "detail": "Punto fuera de los límites de control.",
            }
        )
    if extended:
        for end in range(8, len(y)):
            window = y[end - 8 : end + 1]
            if np.all(window > center) or np.all(window < center):
                results.append(
                    {
                        "index": end,
                        "point": labels[end],
                        "chart": chart,
                        "rule": "Racha de 9",
                        "detail": f"9 puntos del mismo lado de la media: {labels[end - 8]} a {labels[end]}.",
                    }
                )
        for end in range(5, len(y)):
            diff = np.diff(y[end - 5 : end + 1])
            if np.all(diff > 0) or np.all(diff < 0):
                results.append(
                    {
                        "index": end,
                        "point": labels[end],
                        "chart": chart,
                        "rule": "Tendencia de 6",
                        "detail": f"6 puntos consecutivos crecientes o decrecientes: {labels[end - 5]} a {labels[end]}.",
                    }
                )
    return results


def capability(values, center, sigma, lsl, usl, stable):
    if lsl is None and usl is None:
        return None
    for limit in (lsl, usl):
        if limit is not None and not np.isfinite(limit):
            raise ValueError("Los límites de especificación deben ser finitos.")
    if lsl is not None and usl is not None and lsl >= usl:
        raise ValueError("El límite inferior de especificación debe ser menor que el superior.")
    overall = float(np.std(values, ddof=1))
    if sigma <= 0 or overall <= 0:
        return {"unavailable": "No se puede estimar capacidad con variación nula."}
    cpu = (usl - center) / (3 * sigma) if usl is not None else None
    cpl = (center - lsl) / (3 * sigma) if lsl is not None else None
    ppu = (usl - center) / (3 * overall) if usl is not None else None
    ppl = (center - lsl) / (3 * overall) if lsl is not None else None
    pvalue = float(shapiro(values).pvalue) if 3 <= len(values) <= 5000 else None
    outside = np.zeros(len(values), dtype=bool)
    ppm = 0.0
    if lsl is not None:
        outside |= values < lsl
        ppm += norm.cdf((lsl - center) / overall) * 1e6
    if usl is not None:
        outside |= values > usl
        ppm += norm.sf((usl - center) / overall) * 1e6
    return {
        "cp": (usl - lsl) / (6 * sigma) if lsl is not None and usl is not None else None,
        "cpk": min(v for v in (cpu, cpl) if v is not None),
        "pp": (usl - lsl) / (6 * overall) if lsl is not None and usl is not None else None,
        "ppk": min(v for v in (ppu, ppl) if v is not None),
        "sigma_within": sigma,
        "sigma_total": overall,
        "normality_p": pvalue,
        "stable": stable,
        "observed_pct": float(outside.mean() * 100),
        "normal_ppm": float(ppm),
    }


def analyze(frame, config):
    chart = config.get("chart")
    if chart == "pareto":
        category = config.get("value")
        if category not in frame:
            raise ValueError("Selecciona la columna de categorías.")
        labels = frame[category].astype(str).str.strip()
        if (labels == "").any():
            raise ValueError("Las categorías no pueden estar vacías.")
        count_col = config.get("frequency")
        counts = (
            numeric_column(frame, count_col, config.get("decimal", ".")) if count_col else np.ones(len(frame))
        )
        if np.any(counts < 0) or np.any(counts != np.floor(counts)) or counts.sum() == 0:
            raise ValueError("Las frecuencias deben ser enteras no negativas, con un total mayor que cero.")
        totals = {}
        for label, count in zip(labels, counts):
            totals[label] = totals.get(label, 0) + float(count)
        items = sorted(totals.items(), key=lambda item: -item[1])
        return {
            "chart": chart,
            "labels": [a for a, b in items],
            "counts": [b for a, b in items],
            "total": int(sum(counts)),
            "signals": [],
            "warnings": [],
            "config": config,
        }
    if chart not in {"xr", "xs", "imr"}:
        raise ValueError("Selecciona un gráfico válido.")
    groups, labels = make_groups(frame, config)
    if len(groups) < 2:
        raise ValueError("Se requieren al menos dos subgrupos u observaciones.")
    sizes = {len(g) for g in groups}
    if len(sizes) != 1:
        raise ValueError(
            "Los subgrupos tienen tamaños diferentes. Esta versión requiere igual tamaño para X̄–R y X̄–S; completa los grupos o usa I–MR si corresponde al muestreo."
        )
    n = len(groups[0])
    if chart == "xr" and n not in D2:
        raise ValueError("X̄–R admite de 2 a 25 mediciones por subgrupo. Para grupos mayores usa X̄–S.")
    if chart == "xs" and not 2 <= n <= 100:
        raise ValueError("X̄–S requiere de 2 a 100 mediciones por subgrupo.")
    k = config.get("baseline")
    if k is None:
        k = len(groups)
    if not isinstance(k, (int, float)) or int(k) != k or not 2 <= k <= len(groups):
        raise ValueError("La referencia debe contener entre 2 y el total de subgrupos, sin decimales.")
    k = int(k)
    matrix = np.array(groups)
    means = matrix.mean(axis=1)
    center = float(means[:k].mean())
    values = matrix.ravel()
    if chart == "xr":
        dispersion = np.ptp(matrix, axis=1)
        dcenter = float(dispersion[:k].mean())
        sigma = dcenter / D2[n]
        dlower, dupper = D3[n] * dcenter, D4[n] * dcenter
        name = "Rango"
    elif chart == "xs":
        dispersion = matrix.std(axis=1, ddof=1)
        dcenter = float(dispersion[:k].mean())
        sigma = dcenter / c4(n)
        factor = 3 * math.sqrt(1 - c4(n) ** 2) / c4(n)
        dlower, dupper = max(0, 1 - factor) * dcenter, (1 + factor) * dcenter
        name = "Desviación estándar"
    else:
        dispersion = np.abs(np.diff(means))
        dcenter = float(dispersion[: k - 1].mean())
        sigma = dcenter / D2[2]
        dlower, dupper = 0.0, D4[2] * dcenter
        name = "Rango móvil"
    if sigma <= 0:
        raise ValueError(
            "La referencia tiene variación interna nula. Revisa la resolución de las mediciones o selecciona otra referencia."
        )
    lower, upper = center - 3 * sigma / math.sqrt(n), center + 3 * sigma / math.sqrt(n)
    dlabs = labels[1:] if chart == "imr" else labels
    alerts = signals(
        means,
        center,
        lower,
        upper,
        labels,
        config.get("rules", False),
        "Individuales" if chart == "imr" else "Media",
    )
    secondary = signals(dispersion, dcenter, dlower, dupper, dlabs, chart=name)
    for alert in secondary:
        if chart == "imr":
            alert["index"] += 1
    alerts += secondary
    baseline_stable = not any(a["index"] < k for a in alerts)
    warnings = []
    if k < 25:
        warnings.append(
            f"Referencia de {k} puntos: resultados exploratorios. Procura reunir al menos 25 subgrupos representativos."
        )
    if not baseline_stable:
        warnings.append(
            "La referencia presenta señales de causas especiales. Investígalas antes de usar sus límites para seguimiento."
        )
    cap = capability(matrix[:k].ravel(), center, sigma, config.get("lsl"), config.get("usl"), baseline_stable)
    if cap and not cap.get("unavailable"):
        if cap["normality_p"] is not None and cap["normality_p"] < 0.05:
            warnings.append(
                "Shapiro–Wilk sugiere desviación de normalidad (p < 0,05). Los índices normales y los PPM modelados requieren cautela."
            )
        warnings.append(
            "La capacidad describe solo la referencia. Shapiro–Wilk no demuestra normalidad ni independencia; revisa también el gráfico Q–Q y el muestreo."
        )
    return {
        "chart": chart,
        "labels": labels,
        "means": means.tolist(),
        "dispersion": dispersion.tolist(),
        "dispersion_labels": dlabs,
        "dispersion_name": name,
        "center": center,
        "lower": lower,
        "upper": upper,
        "dcenter": dcenter,
        "dlower": dlower,
        "dupper": dupper,
        "sigma": sigma,
        "n": n,
        "baseline": k,
        "total": len(values),
        "values": values.tolist(),
        "reference_values": matrix[:k].ravel().tolist(),
        "signals": alerts,
        "capability": cap,
        "warnings": warnings,
        "config": config,
    }
