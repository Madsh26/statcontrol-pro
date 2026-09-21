# Arquitectura

`src/statcontrol` es el único paquete de aplicación. Se mantienen módulos pequeños por responsabilidad; se pueden convertir en subpaquetes si crece el alcance.

| Módulo | Responsabilidad |
|---|---|
| `data.py` | Lectura de CSV/XLSX/TSV/TXT, detección y validación, subgrupos y proyectos |
| `statistics.py` | Cálculos numéricos puros, capacidad y reglas |
| `figures.py` | Figuras Plotly sin estado mutable compartido |
| `reports.py` | CSV, Excel, PDF y proyectos JSON |
| `ui.py` | Componentes, pantallas y guía de formatos |
| `app.py` | Factoría Dash, callbacks y arranque |
| `assets/styles.css` | Diseño adaptable y estilos |

Flujo: fuente → lectura y vista previa → configuración → validación → cálculo → visualización / exportación.

Tres `dcc.Store` en memoria de pestaña mantienen la fuente, el conjunto interpretado y el resultado. No hay un DataFrame global compartido entre usuarios. Cambiar datos o parámetros invalida el resultado y deshabilita exportaciones hasta repetir el análisis.

Los proyectos usan el esquema `statcontrol/1`, contienen datos y parámetros legibles y se recalculan al abrirlos. No se usa pickle ni ejecución de código de archivos importados. CSV/Excel exportados neutralizan etiquetas que podrían interpretarse como fórmulas.

El diseño local utiliza `127.0.0.1:8050` y no requiere credenciales. Para desplegar en Internet hay que configurar un servidor WSGI, HTTPS, límites de recursos y, si los datos son privados, autenticación. Publicar el repositorio no publica un servicio web.
