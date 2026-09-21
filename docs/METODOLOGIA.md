# Método estadístico y alcance

La app utiliza límites Shewhart a tres desviaciones estándar. El orden de las mediciones se conserva; los identificadores de grupo se procesan en su orden de primera aparición. Los datos originales no se alteran ni se completan automáticamente.

## Referencia y seguimiento

Los primeros `k` puntos forman la referencia (todos, si no se especifica `k`). Los límites quedan fijados con esa referencia. El resto se evalúa contra ellos. La capacidad, distribución, prueba de normalidad y desviación global se calculan exclusivamente con la referencia.

En I–MR, los rangos móviles de referencia son únicamente las diferencias entre sus observaciones: `k−1` rangos. La primera diferencia de seguimiento se muestra, pero no se utiliza para estimar los límites. Las reglas de secuencia se evalúan sobre la serie completa, incluso al cruzar la frontera entre fases.

## Estimadores

| Gráfico | Sigma interna | Límites del gráfico principal |
|---|---|---|
| X̄–R | R̄/d₂(n) | Media de referencia ± 3 sigma/√n |
| X̄–S | S̄/c₄(n) | Media de referencia ± 3 sigma/√n |
| I–MR | MR̄/1,128 | Media de referencia ± 3 sigma |

R usa D₃R̄ y D₄R̄. S usa `S̄ · (1 ± 3√(1−c₄²)/c₄)`; su límite inferior se trunca en cero. MR usa cero y `3,267·MR̄`. Los límites inferiores del gráfico de medias/individuales NO se truncan.

`c₄(n) = √(2/(n−1)) · Γ(n/2)/Γ((n−1)/2)` se evalúa con logaritmos gamma. Las desviaciones muestrales utilizan `ddof=1`. Las tablas d₂, D₃ y D₄ están redondeadas a tres decimales; diferencias menores respecto de tablas o bibliotecas con otra precisión son esperables.

X̄–R admite tamaños de 2 a 25, X̄–S de 2 a 100. Ambos requieren subgrupos iguales. I–MR usa una columna ordenada de observaciones individuales. No se adapta silenciosamente un grupo desigual usando su tamaño mediano.

## Señales

- Punto estrictamente fuera de LCI/LCS en ambos gráficos.
- Opcional: nueve puntos estrictamente del mismo lado de la media.
- Opcional: seis puntos estrictamente crecientes o decrecientes.

Las dos reglas de secuencia se aplican solo a medias/individuales. Empates interrumpen la tendencia; puntos exactamente en la media interrumpen la racha. Una señal de secuencia se registra en su punto final. Ventanas solapadas pueden generar varios eventos. El indicador de puntos con señal elimina duplicados entre reglas y gráficos.

La app implementa este subconjunto de reglas de Nelson, no las ocho reglas completas ni el conjunto Western Electric. Ausencia de señales no prueba estabilidad o independencia.

## Capacidad y desempeño

`Cp = (LSE−LIE)/(6 sigma_interna)`; `Cpk = min((LSE−media)/(3 sigma_interna), (media−LIE)/(3 sigma_interna))`.

Pp/Ppk sustituyen sigma interna por la desviación muestral de todas las observaciones de referencia. Con una sola especificación, Cp/Pp no se calculan y Cpk/Ppk utilizan el lado disponible. Se permiten índices negativos cuando la media queda fuera de especificación.

Se informa la fracción observada fuera de especificaciones y los PPM estimados con una distribución normal ajustada usando la desviación global. Estos PPM son un modelo, no un conteo observado. Shapiro–Wilk se calcula entre 3 y 5.000 observaciones y se acompaña de histograma y gráfico Q–Q. Ni una prueba no significativa ni un Cpk alto prueban adecuación del proceso.

## Validación y limitaciones

La suite verifica casos calculables a mano (X̄–R, X̄–S, I–MR y capacidad), invarianza de límites al cambiar el seguimiento, reglas, validaciones, formatos y exportaciones. En el equipo de desarrollo R está instalado, pero `qcc` no estaba disponible: no se afirma una comparación ejecutada contra ese paquete. La versión anterior usa estimadores y reglas que pueden diferir; sus números no se copian como verdad de referencia.

No incluye capacidad no normal, intervalos de confianza, gráficos de atributos, EWMA, CUSUM, autenticación o una base de datos multiusuario. Los datos se mantienen por pestaña; guarda el JSON para persistirlos. El servidor local procesa los archivos y no los transmite a servicios de análisis externos.

## Referencias

- [NIST: X̄, R y S](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc311.htm)
- [NIST: individuales y rangos móviles](https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm)
- [NIST: estabilidad](https://www.itl.nist.gov/div898/handbook/ppc/section4/ppc45.htm)
- [NIST: capacidad](https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm)
- [Documentación del autor de qcc](https://luca-scr.r-universe.dev/qcc/qcc.pdf)
