"""Herramientas para revisar supuestos de un diseño completamente al azar."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import levene, probplot, shapiro
from statsmodels.regression.linear_model import RegressionResultsWrapper


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Obtiene los residuos y los valores ajustados de un modelo.

    Args:
        modelo: Modelo lineal ajustado para el experimento.

    Returns:
        DataFrame con una fila por observación y las columnas Ajustados y Residuos.
    """
    # El residuo e_i = y_i - ŷ_i cuantifica el error de cada observación respecto al modelo.
    # ŷ_i es la respuesta estimada por el modelo para la unidad experimental i.
    return pd.DataFrame(
        {
            "Ajustados": modelo.fittedvalues,
            "Residuos": modelo.resid,
        }
    )


def prueba_shapiro(
    residuos: pd.Series | np.ndarray, alfa: float = 0.05
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo que se van a evaluar.
        alfa: Nivel de significancia para formular la conclusión.

    Returns:
        Estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no es válido, hay menos de tres residuos o hay valores no finitos.
    """
    if not 0 < alfa < 1:
        raise ValueError("El nivel alfa debe estar entre cero y uno.")

    # Shapiro-Wilk contrasta H0: los residuos provienen de una distribución normal.
    valores = np.asarray(residuos, dtype=float)
    if valores.size < 3:
        raise ValueError("La prueba de Shapiro-Wilk requiere al menos tres residuos.")
    if not np.isfinite(valores).all():
        raise ValueError("Los residuos deben ser finitos para aplicar Shapiro-Wilk.")
    estadistico, p_valor = shapiro(valores)

    # p < alfa señala evidencia contra la normalidad; p >= alfa no la demuestra.
    if p_valor < alfa:
        conclusion = (
            "Se rechaza la normalidad de los residuos; conviene revisar el gráfico "
            "Q-Q y considerar el efecto de esta desviación en el análisis."
        )
    else:
        conclusion = (
            "No se detecta evidencia suficiente para rechazar la normalidad de los "
            "residuos con el nivel de significancia elegido."
        )
    return float(estadistico), float(p_valor), conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la igualdad de varianzas con la prueba de Levene centrada en medianas.

    Args:
        df: Datos del experimento.
        col_trat: Columna que identifica los tratamientos.
        col_resp: Columna de respuesta numérica.
        alfa: Nivel de significancia para formular la conclusión.

    Returns:
        Estadístico W, p-valor y conclusión en español.

    Raises:
        ValueError: Si alfa no es válido, faltan columnas o hay menos de dos grupos.
    """
    if not 0 < alfa < 1:
        raise ValueError("El nivel alfa debe estar entre cero y uno.")
    if col_trat not in df.columns or col_resp not in df.columns:
        raise ValueError("No se encontraron las columnas de tratamiento y respuesta.")

    # Levene compara H0: las varianzas de respuesta son iguales entre tratamientos.
    grupos = [
        grupo[col_resp].to_numpy(dtype=float)
        for _, grupo in df.groupby(col_trat, observed=True)
    ]
    if len(grupos) < 2:
        raise ValueError("La prueba de Levene requiere al menos dos tratamientos.")
    if any(not np.isfinite(grupo).all() for grupo in grupos):
        raise ValueError("Las respuestas deben ser finitas para aplicar Levene.")

    # center="median" usa desviaciones absolutas respecto a la mediana, con robustez
    # ante asimetrías; la prueba devuelve estadístico y p-valor.
    estadistico, p_valor = levene(*grupos, center="median")

    # p < alfa sugiere varianzas distintas; p >= alfa no prueba que sean idénticas.
    if p_valor < alfa:
        conclusion = (
            "Se rechaza la igualdad de varianzas; hay evidencia de heterogeneidad "
            "entre tratamientos."
        )
    else:
        conclusion = (
            "No se detecta evidencia suficiente para rechazar la igualdad de "
            "varianzas entre tratamientos."
        )
    return float(estadistico), float(p_valor), conclusion


def grafico_residuos_vs_ajustados(datos: pd.DataFrame) -> go.Figure:
    """Crea el gráfico de residuos frente a valores ajustados.

    Args:
        datos: DataFrame de `residuos_y_ajustados`.

    Returns:
        Figura Plotly para inspeccionar patrones y dispersión de los residuos.

    Raises:
        ValueError: Si faltan las columnas requeridas.
    """
    if not {"Ajustados", "Residuos"}.issubset(datos.columns):
        raise ValueError("Se requieren las columnas Ajustados y Residuos.")

    # El patrón esperado es una nube aleatoria alrededor de e_i = 0 y sin forma de embudo.
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=datos["Ajustados"],
            y=datos["Residuos"],
            mode="markers",
            name="Observaciones",
            marker={"color": "#2a7f62", "size": 9},
        )
    )
    figura.add_hline(y=0, line_dash="dash", line_color="gray")
    figura.update_layout(
        title="Residuos frente a valores ajustados",
        xaxis_title="Valores ajustados (ŷ)",
        yaxis_title="Residuos (y − ŷ)",
    )
    return figura


def grafico_qq(residuos: pd.Series | np.ndarray) -> go.Figure:
    """Crea un gráfico Q-Q normal para los residuos del modelo.

    Args:
        residuos: Residuos del modelo que se van a representar.

    Returns:
        Figura Plotly con cuantiles observados y teóricos normales.

    Raises:
        ValueError: Si hay menos de dos residuos o valores no finitos.
    """
    # Q-Q compara cuantiles observados con cuantiles teóricos bajo normalidad.
    valores = np.asarray(residuos, dtype=float)
    if valores.size < 2:
        raise ValueError("El gráfico Q-Q requiere al menos dos residuos.")
    if not np.isfinite(valores).all():
        raise ValueError("Los residuos deben ser finitos para construir el gráfico Q-Q.")

    # probplot calcula cuantiles normales teóricos, cuantiles ordenados y recta de referencia.
    (cuantiles_teoricos, cuantiles_observados), (pendiente, intercepto, _) = probplot(
        valores, dist="norm"
    )
    limites_x = np.array([cuantiles_teoricos.min(), cuantiles_teoricos.max()])
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=cuantiles_teoricos,
            y=cuantiles_observados,
            mode="markers",
            name="Residuos observados",
            marker={"color": "#2a7f62", "size": 9},
        )
    )
    figura.add_trace(
        go.Scatter(
            x=limites_x,
            y=intercepto + pendiente * limites_x,
            mode="lines",
            name="Referencia normal",
            line={"color": "#c44e52", "dash": "dash"},
        )
    )
    figura.update_layout(
        title="Gráfico Q-Q de los residuos",
        xaxis_title="Cuantiles teóricos normales",
        yaxis_title="Cuantiles observados de los residuos",
    )
    return figura
