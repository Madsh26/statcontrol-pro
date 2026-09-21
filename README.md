# StatControl Pro

Aplicación de control estadístico de procesos en Python, con importación asistida y una interfaz profesional en español. Proyecto de Ingeniería Industrial, Universidad del Magdalena.

## Inicio rápido

Requiere Python 3.12 o posterior. Probado localmente con Python 3.14 en Windows.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python app.py
```

Abre **http://127.0.0.1:8050**. También puedes usar `./INICIAR.ps1` en PowerShell. Para reproducir exactamente el entorno probado, instala `requirements-lock.txt` antes de instalar el proyecto con `pip install --no-deps --no-build-isolation -e .`.

En macOS/Linux, sustituye `.venv\Scripts\python` por `.venv/bin/python`. El comando `statcontrol` también está disponible después de instalar el paquete.

## Qué puedes hacer

- Cargar CSV, XLSX, TSV y TXT delimitado; pegar tablas desde Excel.
- Descargar plantillas CSV/Excel con datos sintéticos e instrucciones.
- Revisar encabezados, separador, decimal, hoja y columnas antes de analizar.
- Trabajar con formato largo o ancho, conservando el orden de los datos.
- Generar X̄–R, X̄–S, I–MR y Pareto interactivos.
- Fijar una referencia y evaluar observaciones posteriores sin recalcular sus límites.
- Identificar puntos fuera de límites y, opcionalmente, rachas de 9 y tendencias de 6.
- Calcular Cp, Cpk, Pp y Ppk, revisar histograma, Q–Q y normalidad.
- Descargar CSV, Excel, gráficos PNG desde la barra de Plotly e informe PDF.
- Guardar datos y configuración como proyecto JSON y reabrirlo.

No se descartan mediciones incompletas ni se imputan valores. Un archivo inválido muestra un mensaje con el problema y, cuando corresponde, las filas afectadas. Cambiar datos o parámetros invalida resultados y exportaciones anteriores.

## Formato de entrada

**Largo: una medición por fila.**

```csv
subgrupo,medicion
1,100.2
1,100.1
2,99.9
2,100.3
```

**Ancho: un subgrupo por fila.**

```csv
subgrupo,m1,m2,m3
1,100.2,100.1,99.9
2,99.8,100.3,100.0
```

Para coma decimal, usa punto y coma como separador: `1;100,2`. No uses separadores de miles. En Excel, una tabla por hoja, encabezados únicos y sin celdas combinadas. Guarda las fórmulas desde Excel para que sus resultados estén disponibles. Convierte archivos XLS a XLSX.

La detección automática es orientativa: confirma la vista previa. Puedes indicar explícitamente que el archivo tiene o no encabezados. Los límites son 10 MB, 20.000 filas, 100 columnas y 100.000 celdas. X̄–R admite n=2–25 y X̄–S n=2–100; ambos requieren tamaños iguales. Consulta la sección **Guía de formatos** de la app para ejemplos completos.

## Organización

```text
src/statcontrol/   Aplicación, motor, importación, interfaz y exportaciones
examples/         Ejemplos sintéticos y conjunto de referencia migrado
tests/            Pruebas estadísticas, de importación e integración
docs/             Método, arquitectura y registro de migración
.github/workflows/ Comprobaciones automáticas
```

- [Método y limitaciones](docs/METODOLOGIA.md)
- [Arquitectura](docs/ARQUITECTURA.md)
- [Migración](docs/MIGRACION.md)

## Desarrollo

```powershell
.venv\Scripts\python -m pip install -e '.[dev]'
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check src tests
.venv\Scripts\python -m ruff format --check src tests
```

Los cálculos no dependen de Dash. Las pruebas incluyen casos calculados a mano, formatos ambiguos, rechazo de datos incompletos, referencia fija, reglas y exportaciones. GitHub Actions ejecuta la suite con Python 3.12 y 3.14.

## Datos y alcance

Los archivos se procesan en el servidor de la app. Las sesiones se mantienen separadas por pestaña; no existe un DataFrame global compartido. Guarda un proyecto antes de cerrar o recargar. No se usa un servicio externo de análisis. La tipografía puede solicitarse a Google Fonts; si no hay conexión, se usan fuentes del sistema.

La app no declara capacidad por un semáforo aislado: muestra advertencias cuando la referencia tiene señales o el modelo normal requiere revisión. Los índices describen la referencia, no los datos de seguimiento.

El repositorio público contiene código y ejemplos; **no implica que la app esté desplegada públicamente**. El arranque predeterminado escucha solo en este equipo. Para alojamiento público se necesita un servidor WSGI, HTTPS y controles de acceso adecuados al uso.
