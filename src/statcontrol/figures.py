import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm, probplot

BLUE = "#2864ea"
RED = "#dc5263"


def theme(fig, title=None):
    fig.update_layout(
        template="plotly_white",
        title=title,
        font=dict(family="Inter, Segoe UI, sans-serif", color="#44516a", size=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=55, r=60, t=35, b=50),
        height=330,
        hovermode="closest",
        legend=dict(orientation="h", y=1.16, x=0),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(gridcolor="#edf1f7", zeroline=False),
    )
    return fig


def empty(message="Carga tus datos y ejecuta un análisis"):
    fig = theme(go.Figure())
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=15, color="#8b96aa"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def control_figure(result, secondary=False):
    y = result["dispersion" if secondary else "means"]
    labels = result["dispersion_labels" if secondary else "labels"]
    lo, mid, hi = (
        result[k] for k in (("dlower", "dcenter", "dupper") if secondary else ("lower", "center", "upper"))
    )
    name = (
        result["dispersion_name"] if secondary else ("Individuales" if result["chart"] == "imr" else "Media")
    )
    offset = 1 if secondary and result["chart"] == "imr" else 0
    x = list(range(1 + offset, len(y) + 1 + offset))
    fig = theme(go.Figure())
    fig.add_hrect(y0=lo, y1=hi, fillcolor="#f3f7ff", line_width=0, layer="below")
    for value, color, dash, label in [
        (hi, RED, "dash", "LCS"),
        (mid, "#8a9ab6", "dot", "LC"),
        (lo, RED, "dash", "LCI"),
    ]:
        fig.add_hline(
            y=value,
            line_color=color,
            line_dash=dash,
            line_width=1,
            annotation_text=f"{label} {value:.3f}",
            annotation_position="right",
        )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            customdata=labels,
            mode="lines+markers",
            name=name,
            line=dict(color=BLUE, width=2),
            marker=dict(size=6),
            hovertemplate="Subgrupo %{customdata}<br>Valor: %{y:.4f}<extra></extra>",
        )
    )
    marked = sorted({a["index"] - offset for a in result["signals"] if a["chart"] == name})
    if marked:
        fig.add_trace(
            go.Scatter(
                x=[x[i] for i in marked],
                y=[y[i] for i in marked],
                mode="markers",
                name="Señal detectada",
                marker=dict(size=10, color=RED, line=dict(color="white", width=2)),
                customdata=[labels[i] for i in marked],
                hovertemplate="Señal · %{customdata}<br>%{y:.4f}<extra></extra>",
            )
        )
    if result["baseline"] < len(result["labels"]):
        fig.add_vline(
            x=result["baseline"] + 0.5, line_dash="dot", line_color="#7985a0", annotation_text="Seguimiento →"
        )
    fig.update_xaxes(title="Orden de observación", rangemode="tozero")
    fig.update_yaxes(title=name)
    return fig


def pareto_figure(result):
    labels, counts = result["labels"], result["counts"]
    cumulative = np.cumsum(counts) / sum(counts) * 100
    fig = theme(go.Figure(go.Bar(x=labels, y=counts, name="Frecuencia", marker_color=BLUE)))
    fig.add_trace(
        go.Scatter(
            x=labels, y=cumulative, name="% acumulado", yaxis="y2", mode="lines+markers", line_color="#e9aa38"
        )
    )
    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right", range=[0, 105], title="% acumulado", showgrid=False),
        height=450,
    )
    fig.update_yaxes(title="Frecuencia", secondary_y=None)
    return fig


def distribution_figures(result):
    vals = result["reference_values"]
    fig = theme(
        go.Figure(
            go.Histogram(
                x=vals,
                histnorm="probability density",
                name="Mediciones",
                marker_color="#84a6fa",
                opacity=0.85,
            )
        )
    )
    std = float(np.std(vals, ddof=1))
    if std > 0:
        xs = np.linspace(min(vals) - std, max(vals) + std, 150)
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=norm.pdf(xs, np.mean(vals), std),
                name="Normal ajustada",
                line=dict(color=BLUE, width=2),
            )
        )
    for key, label in [("lsl", "LIE"), ("usl", "LSE")]:
        value = result["config"].get(key)
        if value is not None:
            fig.add_vline(x=value, line_color=RED, line_dash="dash", annotation_text=label)
    fig.update_xaxes(title="Medición")
    fig.update_yaxes(title="Densidad")
    (theoretical, observed), (slope, intercept, _) = probplot(vals, dist="norm")
    qq = theme(
        go.Figure(
            go.Scatter(
                x=theoretical, y=observed, mode="markers", name="Mediciones", marker=dict(color=BLUE, size=5)
            )
        )
    )
    qq.add_trace(
        go.Scatter(
            x=theoretical,
            y=slope * theoretical + intercept,
            mode="lines",
            name="Referencia normal",
            line=dict(color=RED, dash="dash"),
        )
    )
    qq.update_xaxes(title="Cuantiles normales teóricos")
    qq.update_yaxes(title="Cuantiles observados")
    return fig, qq
