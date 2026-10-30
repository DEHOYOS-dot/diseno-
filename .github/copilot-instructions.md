# Instrucciones para Copilot

## Contexto del proyecto

Este repositorio contiene una aplicación de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental del programa de Ingeniería Agrícola de la Universidad de Sucre.

## Estructura del proyecto

- `app.py`: portada de la aplicación.
- `pages/`: una página por cada diseño experimental.
- `utils/`: funciones reutilizables; debe incluir `__init__.py`.
- `data/`: archivos CSV de ejemplo.
- `verificacion/`: scripts de R para verificar los análisis.

Respeta esta estructura al agregar o modificar funcionalidades.

## Idioma y orientación educativa

- Escribe en español todo el código nuevo, los comentarios, los docstrings y los mensajes de la interfaz.
- Añade un comentario en cada paso estadístico para explicar qué calcula y por qué, con explicaciones adecuadas para estudiantes de Ingeniería Agrícola.
- No inventes ni simules resultados. Todos los números mostrados deben proceder del cálculo realizado con los datos correspondientes.

## Código y documentación

- Incluye anotaciones de tipos (`type hints`) en las funciones.
- Escribe los docstrings de las funciones en español y con el estilo Google.
- Sigue los patrones y convenciones que ya use el repositorio.

## Dependencias y métodos estadísticos

- Las únicas librerías permitidas son `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`.
- No agregues otras librerías ni dependencias sin pedir permiso.
- Ajusta los modelos ANOVA con `statsmodels.formula.api.ols` y calcula la tabla con `statsmodels.stats.anova.anova_lm(typ=2)`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.

## Verificación

Antes de terminar una tarea, ejecuta el código afectado y corrige los errores que aparezcan. No declares una tarea verificada si no has ejecutado la comprobación correspondiente.
