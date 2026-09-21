from dash import dcc, html

from .figures import empty

GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "responsive": True,
}


def field(label, component, hint=None):
    return html.Div(
        [html.Label(label, htmlFor=component.id), component, html.Small(hint) if hint else None],
        className="field",
    )


def dropdown(id, options=None, value=None, **kwargs):
    return dcc.Dropdown(
        id=id, options=options or [], value=value, clearable=kwargs.pop("clearable", False), **kwargs
    )


def card(title, content, subtitle=None, **kwargs):
    return html.Section(
        [
            html.Div(
                [html.H3(title), html.P(subtitle, className="muted") if subtitle else None],
                className="card-heading",
            ),
            content,
        ],
        className="card",
        **kwargs,
    )


def table(frame, limit=12):
    return html.Div(
        html.Table(
            [
                html.Thead(html.Tr([html.Th(str(c)) for c in frame.columns])),
                html.Tbody(
                    [
                        html.Tr([html.Td(str(v)) for v in row])
                        for row in frame.head(limit).itertuples(index=False, name=None)
                    ]
                ),
            ]
        ),
        className="table-scroll",
    )


def metric(label, value, hint, accent=False):
    return html.Div(
        [
            html.Div(label, className="metric-label"),
            html.Div(value, className="metric-value"),
            html.Div(hint, className="metric-hint"),
        ],
        className="metric" + (" accent" if accent else ""),
    )


GUIDE = """
**Formatos admitidos:** CSV, XLSX, TSV y TXT delimitado. Máximo 10 MB, 20.000 filas, 100 columnas y 100.000 celdas. Convierte `.xls` a `.xlsx`.

### Formato largo: una medición por fila
```csv
subgrupo,medicion
1,100.2
1,100.1
2,99.9
2,100.3
```
Selecciona **medicion** como valor y **subgrupo** como identificador. Cada grupo debe tener la misma cantidad de mediciones, al menos dos. El orden de primera aparición de los grupos se conserva. Sin identificador, se forman grupos consecutivos del tamaño elegido.

### Formato ancho: un subgrupo por fila
```csv
subgrupo,m1,m2,m3
1,100.2,100.1,99.9
2,99.8,100.3,100.0
```
Elige **Ancho**, selecciona únicamente **m1, m2, m3** como mediciones y **subgrupo** como identificador. No incluyas la ID entre las mediciones. Cada ID debe ser única.

### Coma decimal
```text
subgrupo;medicion
1;100,2
1;100,1
```
Usa **punto y coma** como separador y **coma** como decimal. Evita separadores de miles. Un archivo de una sola columna con coma decimal es ambiguo: selecciona punto y coma como separador y revisa la vista previa.

### Excel
Primera fila con nombres únicos, sin títulos adicionales ni celdas combinadas. Una tabla por hoja. Selecciona la hoja que vas a analizar. Usa celdas numéricas y guarda el archivo desde Excel si contiene fórmulas; la app lee sus resultados almacenados. No selecciones hojas de instrucciones.

### Individuales y Pareto
**I–MR:** selecciona una columna numérica en orden temporal. Cada fila es una observación, sin agrupar. Las opciones de agrupación se ignoran.

**Pareto:** selecciona una columna de categorías y, opcionalmente, una de frecuencias enteras no negativas. Sin frecuencia, cada fila cuenta una ocurrencia. No se calculan límites de control ni capacidad.

### Antes de analizar
1. Revisa el separador, la hoja y si la primera fila es un encabezado.
2. Verifica la vista previa y el total de filas.
3. Selecciona las columnas correctas; no se convierten fechas o categorías en mediciones.
4. Corrige celdas vacías, texto y subgrupos incompletos en el archivo original.
5. Conserva el orden de toma de las mediciones. No ordenes por su magnitud.

La detección automática es una sugerencia. No se imputan valores ni se descartan mediciones inválidas. Los proyectos se mantienen en la memoria de esta pestaña; guarda un proyecto antes de cerrarla o recargarla.
"""


def layout():
    return html.Div(
        [
            dcc.Store(id="nav-scroll"),
            dcc.Store(id="source", storage_type="memory"),
            dcc.Store(id="dataset", storage_type="memory"),
            dcc.Store(id="result", storage_type="memory"),
            dcc.Download(id="download"),
            dcc.Download(id="template-download"),
            html.Aside(
                [
                    html.Div(
                        [
                            html.Div("S", className="brand-icon"),
                            html.Div(
                                [
                                    html.Strong("StatControl"),
                                    html.Span("PRO / ANALYTICS", className="brand-sub"),
                                ]
                            ),
                        ],
                        className="brand",
                    ),
                    html.Div("ESPACIO DE ANÁLISIS", className="nav-caption"),
                    dcc.Tabs(
                        id="nav",
                        value="data",
                        vertical=True,
                        className="navigation",
                        children=[
                            dcc.Tab(
                                label=label,
                                value=value,
                                className="nav-tab",
                                selected_className="nav-tab selected",
                            )
                            for label, value in [
                                ("01   Datos y preparación", "data"),
                                ("02   Control del proceso", "analysis"),
                                ("03   Capacidad y distribución", "capacity"),
                                ("04   Informes y proyectos", "reports"),
                                ("05   Guía de formatos", "guide"),
                            ]
                        ],
                    ),
                    html.Div(
                        [
                            html.Div("Hecho para entender tu proceso", className="sidebar-note"),
                            html.P("De las mediciones a las decisiones, con cada cálculo a la vista."),
                            html.Div("INGENIERÍA INDUSTRIAL", className="nav-caption"),
                            html.Span("Universidad del Magdalena", className="university"),
                        ],
                        className="sidebar-bottom",
                    ),
                ],
                className="sidebar",
            ),
            html.Main(
                [
                    html.Header(
                        [
                            html.Div(
                                [
                                    html.Span("WORKSPACE", className="eyebrow"),
                                    html.Span(" / Control estadístico de procesos", className="breadcrumb"),
                                ]
                            ),
                            html.Div(
                                [html.Span(className="status-dot"), "Sesión local · v1.0"],
                                className="session-badge",
                            ),
                        ],
                        className="topbar",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div("PRECISIÓN EN CADA DECISIÓN", className="eyebrow"),
                                            html.H1("Conoce la historia de tu proceso."),
                                            html.P(
                                                "Prepara tus datos, identifica variaciones y convierte los resultados en acciones.",
                                                className="lead",
                                            ),
                                        ]
                                    ),
                                    html.Button(
                                        "↗  Explorar un ejemplo", id="demo", className="button secondary"
                                    ),
                                ],
                                className="page-heading",
                            ),
                            html.Div(id="load-status", role="status"),
                            html.Div(
                                id="data-section",
                                children=[
                                    html.Div(
                                        [
                                            card(
                                                "01 / Tu punto de partida",
                                                html.Div(
                                                    [
                                                        dcc.Upload(
                                                            id="upload",
                                                            accept=".csv,.xlsx,.tsv,.txt",
                                                            multiple=False,
                                                            children=html.Div(
                                                                [
                                                                    html.Div("↑", className="upload-icon"),
                                                                    html.H3("Arrastra tu archivo aquí"),
                                                                    html.P(
                                                                        [
                                                                            "o ",
                                                                            html.Strong(
                                                                                "selecciónalo desde tu equipo"
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    html.Span(
                                                                        "CSV · EXCEL · TSV · TXT   /   HASTA 10 MB",
                                                                        className="file-types",
                                                                    ),
                                                                ]
                                                            ),
                                                            className="upload-area",
                                                        ),
                                                        html.Div(
                                                            [
                                                                html.Span(
                                                                    "¿Empiezas desde cero?", className="muted"
                                                                ),
                                                                html.Button(
                                                                    "Plantilla CSV",
                                                                    id="template-csv",
                                                                    className="text-button",
                                                                ),
                                                                html.Button(
                                                                    "Plantilla Excel",
                                                                    id="template-xlsx",
                                                                    className="text-button",
                                                                ),
                                                            ],
                                                            className="template-row",
                                                        ),
                                                        html.Details(
                                                            [
                                                                html.Summary(
                                                                    "Pegar datos desde Excel o escribirlos"
                                                                ),
                                                                dcc.Textarea(
                                                                    id="manual",
                                                                    placeholder="subgrupo\tmedicion\n1\t100.2\n1\t100.1\n2\t99.9\n2\t100.3",
                                                                    className="manual-input",
                                                                ),
                                                                html.Button(
                                                                    "Leer estos datos",
                                                                    id="manual-load",
                                                                    className="button secondary",
                                                                ),
                                                            ],
                                                            className="manual-block",
                                                        ),
                                                    ]
                                                ),
                                                "Importación asistida, con vista previa antes de calcular.",
                                            ),
                                            html.Section(
                                                [
                                                    html.Span(
                                                        "UN FORMATO CLARO, UN ANÁLISIS MEJOR",
                                                        className="eyebrow",
                                                    ),
                                                    html.H2("Tus datos,\nsin adivinanzas."),
                                                    html.P(
                                                        "Una fila por medición o una fila por subgrupo. Tú eliges; la app te ayuda a interpretarlo."
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Span("1", className="step-circle"),
                                                            html.Span("Carga o pega tus mediciones"),
                                                        ],
                                                        className="intro-step",
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Span("2", className="step-circle"),
                                                            html.Span("Revisa columnas y formato"),
                                                        ],
                                                        className="intro-step",
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Span("3", className="step-circle"),
                                                            html.Span("Configura y analiza"),
                                                        ],
                                                        className="intro-step",
                                                    ),
                                                    html.Div(
                                                        "No se eliminan mediciones incompletas de forma automática.",
                                                        className="intro-foot",
                                                    ),
                                                ],
                                                className="intro-card",
                                            ),
                                        ],
                                        className="import-grid",
                                    ),
                                    card(
                                        "02 / Revisa la lectura",
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        field(
                                                            "Separador de texto",
                                                            dropdown(
                                                                "separator",
                                                                [
                                                                    {"label": label, "value": value}
                                                                    for label, value in [
                                                                        ("Detectar automáticamente", "auto"),
                                                                        ("Coma (,)", ","),
                                                                        ("Punto y coma (;)", ";"),
                                                                        ("Tabulación", "\t"),
                                                                        ("Barra (|)", "|"),
                                                                    ]
                                                                ],
                                                                "auto",
                                                            ),
                                                        ),
                                                        field(
                                                            "Primera fila",
                                                            dropdown(
                                                                "header",
                                                                [
                                                                    {
                                                                        "label": "Detectar encabezados",
                                                                        "value": "auto",
                                                                    },
                                                                    {
                                                                        "label": "Contiene nombres de columnas",
                                                                        "value": "yes",
                                                                    },
                                                                    {
                                                                        "label": "Contiene datos",
                                                                        "value": "no",
                                                                    },
                                                                ],
                                                                "auto",
                                                            ),
                                                        ),
                                                        field(
                                                            "Hoja de Excel",
                                                            dropdown(
                                                                "sheet",
                                                                clearable=True,
                                                                placeholder="Primera hoja",
                                                            ),
                                                        ),
                                                    ],
                                                    className="form-grid three",
                                                ),
                                                html.Div(id="read-notes"),
                                                html.Div(
                                                    id="preview",
                                                    children=html.Div(
                                                        "La vista previa aparecerá al cargar tus datos.",
                                                        className="empty-state",
                                                    ),
                                                ),
                                                html.Div(id="data-summary", className="preview-footer"),
                                            ]
                                        ),
                                        "Comprueba que la primera medición no se haya convertido en encabezado.",
                                    ),
                                    card(
                                        "03 / Define tu análisis",
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        field(
                                                            "Tipo de gráfico",
                                                            dropdown(
                                                                "chart",
                                                                [
                                                                    {"label": label, "value": value}
                                                                    for label, value in [
                                                                        ("X̄–R · Medias y rangos", "xr"),
                                                                        ("X̄–S · Medias y desviaciones", "xs"),
                                                                        (
                                                                            "I–MR · Individuales y rango móvil",
                                                                            "imr",
                                                                        ),
                                                                        (
                                                                            "Pareto · Categorías y frecuencias",
                                                                            "pareto",
                                                                        ),
                                                                    ]
                                                                ],
                                                                "xr",
                                                            ),
                                                        ),
                                                        field(
                                                            "Organización",
                                                            dropdown(
                                                                "layout",
                                                                [
                                                                    {
                                                                        "label": "Largo · Una medición por fila",
                                                                        "value": "long",
                                                                    },
                                                                    {
                                                                        "label": "Ancho · Un subgrupo por fila",
                                                                        "value": "wide",
                                                                    },
                                                                ],
                                                                "long",
                                                            ),
                                                        ),
                                                        field(
                                                            "Separador decimal",
                                                            dropdown(
                                                                "decimal",
                                                                [
                                                                    {"label": "Punto · 100.25", "value": "."},
                                                                    {"label": "Coma · 100,25", "value": ","},
                                                                ],
                                                                ".",
                                                            ),
                                                            "Excel guarda números con punto; no uses separadores de miles.",
                                                        ),
                                                    ],
                                                    className="form-grid three",
                                                ),
                                                html.Div(
                                                    [
                                                        field(
                                                            "Medición / categoría",
                                                            dropdown(
                                                                "value", placeholder="Seleccionar columna"
                                                            ),
                                                        ),
                                                        field(
                                                            "Identificador del subgrupo",
                                                            dropdown(
                                                                "group",
                                                                clearable=True,
                                                                placeholder="Sin identificador",
                                                            ),
                                                            "Vacío: agrupar por orden. En ancho, una ID única por fila.",
                                                        ),
                                                        field(
                                                            "Tamaño del subgrupo",
                                                            dcc.Input(
                                                                id="size",
                                                                type="number",
                                                                value=5,
                                                                min=2,
                                                                max=100,
                                                                step=1,
                                                            ),
                                                            "Se utiliza en formato largo sin identificador.",
                                                        ),
                                                    ],
                                                    className="form-grid three",
                                                ),
                                                html.Div(
                                                    [
                                                        field(
                                                            "Columnas de medición · formato ancho",
                                                            dropdown("measures", multi=True, clearable=True),
                                                        ),
                                                        field(
                                                            "Frecuencia · solo Pareto",
                                                            dropdown(
                                                                "frequency",
                                                                clearable=True,
                                                                placeholder="Contar una ocurrencia por fila",
                                                            ),
                                                        ),
                                                    ],
                                                    className="form-grid two",
                                                ),
                                                html.Details(
                                                    [
                                                        html.Summary(
                                                            "Referencia, especificaciones y reglas de detección"
                                                        ),
                                                        html.Div(
                                                            [
                                                                field(
                                                                    "Puntos de referencia",
                                                                    dcc.Input(
                                                                        id="baseline",
                                                                        type="number",
                                                                        min=2,
                                                                        step=1,
                                                                        placeholder="Todos",
                                                                    ),
                                                                    "Los primeros k puntos fijan los límites; el resto es seguimiento.",
                                                                ),
                                                                field(
                                                                    "Límite inferior · LIE",
                                                                    dcc.Input(
                                                                        id="lsl",
                                                                        type="number",
                                                                        placeholder="Opcional",
                                                                        step="any",
                                                                    ),
                                                                ),
                                                                field(
                                                                    "Límite superior · LSE",
                                                                    dcc.Input(
                                                                        id="usl",
                                                                        type="number",
                                                                        placeholder="Opcional",
                                                                        step="any",
                                                                    ),
                                                                ),
                                                            ],
                                                            className="form-grid three advanced-grid",
                                                        ),
                                                        dcc.Checklist(
                                                            id="rules",
                                                            options=[
                                                                {
                                                                    "label": " Detectar también rachas de 9 y tendencias de 6 puntos (Nelson 2–3)",
                                                                    "value": "extended",
                                                                }
                                                            ],
                                                            value=["extended"],
                                                            className="checklist",
                                                        ),
                                                        html.P(
                                                            "Los límites de especificación definen requisitos del producto; los de control se calculan con tus datos.",
                                                            className="muted",
                                                        ),
                                                    ],
                                                    open=True,
                                                    className="advanced",
                                                ),
                                                html.Div(
                                                    [
                                                        html.Span(
                                                            "La lectura y los datos se validan antes de calcular.",
                                                            className="muted",
                                                        ),
                                                        html.Button(
                                                            "Analizar proceso  →",
                                                            id="run",
                                                            className="button primary",
                                                            disabled=True,
                                                        ),
                                                    ],
                                                    className="action-bar",
                                                ),
                                            ]
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(id="analysis-status", role="alert"),
                            html.Div(
                                id="analysis-section",
                                style={"display": "none"},
                                children=[
                                    html.Div(
                                        id="metrics",
                                        className="metrics",
                                        children=[
                                            metric("OBSERVACIONES", "—", "A la espera de datos"),
                                            metric("SUBGRUPOS", "—", "Organiza tus mediciones"),
                                            metric("SEÑALES", "—", "Evalúa la estabilidad"),
                                            metric("SIGMA INTERNA", "—", "Variación de referencia", True),
                                        ],
                                    ),
                                    html.Div(id="warnings"),
                                    card(
                                        "Comportamiento del proceso",
                                        dcc.Graph(id="primary-graph", figure=empty(), config=GRAPH_CONFIG),
                                        "Límites de control a 3σ · Acerca el gráfico para explorar cada punto.",
                                    ),
                                    html.Div(
                                        card(
                                            "Variación dentro del proceso",
                                            dcc.Graph(
                                                id="secondary-graph", figure=empty(), config=GRAPH_CONFIG
                                            ),
                                        ),
                                        id="secondary-wrap",
                                    ),
                                    card(
                                        "Señales que merecen atención",
                                        html.Div(
                                            id="signals",
                                            className="empty-state",
                                            children="Ejecuta un análisis para identificar señales.",
                                        ),
                                    ),
                                    card(
                                        "Resultados por subgrupo",
                                        html.Div(id="results-table"),
                                        "Vista de las primeras 20 filas. Descarga la tabla completa en Informes.",
                                    ),
                                ],
                            ),
                            html.Div(
                                id="capacity-section",
                                style={"display": "none"},
                                children=[
                                    html.Div(
                                        id="capacity-content",
                                        className="empty-state",
                                        children="Agrega límites de especificación y analiza el proceso.",
                                    ),
                                    html.Div(
                                        [
                                            card(
                                                "Distribución de la referencia",
                                                dcc.Graph(
                                                    id="histogram", figure=empty(), config=GRAPH_CONFIG
                                                ),
                                            ),
                                            card(
                                                "Gráfico Q–Q normal",
                                                dcc.Graph(id="qq", figure=empty(), config=GRAPH_CONFIG),
                                            ),
                                        ],
                                        className="chart-grid",
                                    ),
                                    card(
                                        "Cómo leer la capacidad",
                                        html.P(
                                            "Cp y Cpk utilizan la variación interna; Pp y Ppk, la desviación global de la referencia. Un valor alto no prueba estabilidad. Revisa primero las señales, el muestreo y la distribución. Con una sola especificación se muestran únicamente los índices unilaterales Cpk y Ppk."
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(
                                id="reports-section",
                                style={"display": "none"},
                                children=[
                                    card(
                                        "Lleva tus resultados contigo",
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.H3("Informe PDF"),
                                                        html.P(
                                                            "Gráficos de control, parámetros e interpretación."
                                                        ),
                                                        html.Button(
                                                            "Descargar PDF",
                                                            id="export-pdf",
                                                            className="button primary",
                                                            disabled=True,
                                                        ),
                                                    ],
                                                    className="export-card",
                                                ),
                                                html.Div(
                                                    [
                                                        html.H3("Libro de resultados"),
                                                        html.P(
                                                            "Tablas completas, señales y configuración del análisis."
                                                        ),
                                                        html.Button(
                                                            "Descargar Excel",
                                                            id="export-xlsx",
                                                            className="button secondary",
                                                            disabled=True,
                                                        ),
                                                        html.Button(
                                                            "Descargar CSV",
                                                            id="export-csv",
                                                            className="text-button",
                                                            disabled=True,
                                                        ),
                                                    ],
                                                    className="export-card",
                                                ),
                                                html.Div(
                                                    [
                                                        html.H3("Proyecto reproducible"),
                                                        html.P(
                                                            "Guarda los datos y parámetros para continuar después."
                                                        ),
                                                        html.Button(
                                                            "Guardar proyecto",
                                                            id="export-project",
                                                            className="button secondary",
                                                            disabled=True,
                                                        ),
                                                    ],
                                                    className="export-card",
                                                ),
                                            ],
                                            className="export-grid",
                                        ),
                                    ),
                                    card(
                                        "Retomar un proyecto",
                                        dcc.Upload(
                                            id="project-upload",
                                            accept=".json",
                                            children=html.Div(
                                                [
                                                    html.Strong("Abrir un proyecto StatControl"),
                                                    html.P(
                                                        "Selecciona el archivo .json guardado. Los resultados se recalculan con la configuración restaurada."
                                                    ),
                                                ]
                                            ),
                                            className="upload-area compact",
                                        ),
                                    ),
                                    html.Div(id="export-status", role="status"),
                                ],
                            ),
                            html.Div(
                                id="guide-section",
                                style={"display": "none"},
                                children=[
                                    card("Un archivo bien preparado, paso a paso", dcc.Markdown(GUIDE))
                                ],
                            ),
                            html.Footer(
                                [
                                    html.Span("STATCONTROL PRO"),
                                    html.Span("Control estadístico con método, claridad y contexto."),
                                ],
                                className="footer",
                            ),
                        ],
                        className="workspace",
                    ),
                ],
                className="main",
            ),
        ],
        className="app-shell",
    )
