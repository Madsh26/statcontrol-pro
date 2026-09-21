# Registro de migración

Se reconstruyó la app como un paquete Python independiente de R y Jupyter. Se revisaron tres scripts R, cuatro notebooks y la implementación Dash previa.

## Funciones conservadas o ampliadas

Carga de archivos, entrada manual por pegado, formatos largo/ancho, gráficos de medias y dispersión, individuales, Pareto, capacidad, tablas y ayuda. Se agregaron plantillas, lectura asistida, referencia fija, proyectos reproducibles, exportaciones y validaciones explícitas.

Las reglas se documentan como Nelson 1–3 en lugar de reutilizar sin revisión la función anterior denominada Western Electric. No se migraron servidores, resultados ni estados de sesión antiguos.

## Correcciones

- Se eliminó la instrucción de shell incrustada en el Python anterior y la doble creación de Dash.
- Se separaron lectura, cálculos, visualización e informes.
- Se reemplazó el estado global de datos por estado independiente de pestaña.
- Los tamaños desiguales e incompletos se rechazan con explicación.
- La capacidad utiliza el estimador correspondiente al gráfico y la referencia seleccionada.
- Se eliminó la clasificación automática de capacidad basada únicamente en un umbral fijo.

## Limpieza

Los originales se respaldaron antes de sobrescribirlos y se verificó la integridad del ZIP. El respaldo se conserva fuera de la carpeta del proyecto y no se publica en GitHub. Se retiran los tres scripts R, cuatro notebooks, .RData, .Rhistory, recursos gráficos no utilizados, documento de presentación antiguo y carpetas de ejemplos duplicadas.

El conjunto numérico de Datos.csv se conserva como `examples/referencia_migrada.csv` con encabezados. Los demás ejemplos se generan para la nueva app. El código fuente vigente está exclusivamente en `src/statcontrol`.
