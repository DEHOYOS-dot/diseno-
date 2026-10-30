"""Funciones reutilizables para el análisis de un diseño completamente al azar."""

from pathlib import Path
from typing import IO
import warnings

import numpy as np
import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd


def cargar_datos(archivo: str | Path | IO[bytes] | IO[str]) -> pd.DataFrame:
    """Carga datos desde un archivo CSV o Excel.

    Args:
        archivo: Ruta o archivo abierto con extensión `.csv` o `.xlsx`.

    Returns:
        Un DataFrame con los datos del archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o Excel `.xlsx`.
    """
    # Se obtiene el nombre para identificar el formato sin alterar el archivo recibido.
    nombre_archivo = str(getattr(archivo, "name", archivo))
    extension = Path(nombre_archivo).suffix.lower()

    # El motor de Python detecta si el CSV usa coma o punto y coma como separador.
    if extension == ".csv":
        return pd.read_csv(archivo, sep=None, engine="python")

    # pandas delega la lectura de Excel al motor openpyxl permitido en el proyecto.
    if extension == ".xlsx":
        return pd.read_excel(archivo, engine="openpyxl")

    # Se informa explícitamente cuando el formato no está entre los admitidos.
    raise ValueError("Formato no compatible. Use un archivo CSV o Excel .xlsx.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida las columnas y las réplicas requeridas para un DCA.

    Args:
        df: Datos que se desean analizar.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.

    Returns:
        Lista de errores en español; queda vacía si los datos son válidos.
    """
    # Se comprueba primero la estructura para evitar accesos a columnas inexistentes.
    errores: list[str] = []
    columnas_faltantes = [
        columna for columna in (col_trat, col_resp) if columna not in df.columns
    ]
    for columna in columnas_faltantes:
        errores.append(f"No se encontró la columna requerida «{columna}».")
    if errores:
        return errores

    # Tratamiento y respuesta deben ser variables distintas para definir el modelo.
    if col_trat == col_resp:
        errores.append("Las columnas de tratamiento y respuesta deben ser distintas.")

    # Se exige una respuesta numérica porque el ANOVA compara medias cuantitativas.
    if not pd.api.types.is_numeric_dtype(df[col_resp]) or pd.api.types.is_bool_dtype(
        df[col_resp]
    ):
        errores.append(f"La columna de respuesta «{col_resp}» debe ser numérica.")

    # Se identifican faltantes en ambas variables porque impiden asignar observaciones.
    if df[[col_trat, col_resp]].isna().any().any():
        errores.append("Hay datos faltantes en las columnas seleccionadas.")

    # Se cuentan tratamientos observados para comprobar que la comparación sea posible.
    numero_tratamientos = df[col_trat].nunique(dropna=True)
    if numero_tratamientos < 2:
        errores.append("Se requieren al menos dos tratamientos.")

    # n_j = número de filas del tratamiento j; cada n_j debe ser al menos dos.
    replicas_por_tratamiento = df[col_trat].value_counts(dropna=True)
    if (replicas_por_tratamiento < 2).any():
        errores.append("Cada tratamiento debe tener al menos dos réplicas.")

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos válidos para el análisis.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta.

    Returns:
        Modelo lineal ajustado por mínimos cuadrados ordinarios.
    """
    # El modelo es y_ij = μ + τ_i + ε_ij; Q() protege nombres con espacios o símbolos.
    formula = f"Q({col_resp!r}) ~ C(Q({col_trat!r}))"

    # El modelo separa la variación entre tratamientos del error experimental.
    return ols(formula, data=df).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II con fuentes en español.

    Args:
        modelo: Modelo lineal ajustado para un DCA.

    Returns:
        Tabla con las fuentes Tratamientos, Error y Total.
    """
    # La suma de cuadrados tipo II evalúa el efecto del tratamiento en el modelo.
    anova = anova_lm(modelo, typ=2)
    filas: list[dict[str, float | str]] = []
    suma_cuadrados_total = 0.0
    grados_libertad_total = 0.0

    # Se traducen las fuentes y se calcula cada cuadrado medio como CM = SC / gl.
    # Statsmodels obtiene F = CM(Tratamientos) / CM(Error) y su p-valor asociado.
    for fuente, valores in anova.iterrows():
        suma_cuadrados = float(valores["sum_sq"])
        grados_libertad = float(valores["df"])
        cuadrado_medio = suma_cuadrados / grados_libertad
        es_error = str(fuente).lower() == "residual"
        filas.append(
            {
                "Fuente": "Error" if es_error else "Tratamientos",
                "gl": grados_libertad,
                "SC": suma_cuadrados,
                "CM": cuadrado_medio,
                "F": float(valores["F"]) if not es_error else np.nan,
                "p-valor": float(valores["PR(>F)"]) if not es_error else np.nan,
            }
        )
        suma_cuadrados_total += suma_cuadrados
        grados_libertad_total += grados_libertad

    # La fila total reúne la variación completa y sus grados de libertad (N - 1).
    filas.append(
        {
            "Fuente": "Total",
            "gl": grados_libertad_total,
            "SC": suma_cuadrados_total,
            "CM": suma_cuadrados_total / grados_libertad_total,
            "F": np.nan,
            "p-valor": np.nan,
        }
    )
    return pd.DataFrame(filas, columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"])


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.

    Returns:
        Tabla ordenada por tratamiento con n, total, media y desviación estándar.
    """
    # Para cada grupo se calculan n_j, total_j = suma(y_ij), media_j = total_j / n_j.
    # La desviación muestral es s_j = sqrt(suma((y_ij - media_j)^2) / (n_j - 1)).
    resumen = df.groupby(col_trat, observed=True).agg(
        n=(col_resp, "count"),
        total=(col_resp, "sum"),
        media=(col_resp, "mean"),
        desviacion_estandar=(col_resp, "std"),
    )

    # Se conserva el nombre original del tratamiento para identificar cada grupo.
    resumen.index.name = col_trat
    resumen = resumen.reset_index()
    return resumen.rename(columns={"desviacion_estandar": "desviación estándar"})


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación del experimento.

    Args:
        modelo: Modelo lineal ajustado para el DCA.
        df: Datos usados para ajustar el modelo.
        col_resp: Nombre de la columna de respuesta.

    Returns:
        Coeficiente de variación expresado como porcentaje.

    Raises:
        ValueError: Si la media general es cero o no es un número finito.
    """
    # El CME estima el error experimental residual a partir de la tabla tipo II.
    anova = anova_lm(modelo, typ=2)
    fila_error = anova.loc[anova.index.astype(str).str.lower() == "residual"].iloc[0]
    cuadrado_medio_error = float(fila_error["sum_sq"] / fila_error["df"])

    # La media general sirve de referencia para expresar el error en porcentaje.
    media_general = float(df[col_resp].mean())
    if not np.isfinite(media_general) or media_general == 0:
        raise ValueError("No se puede calcular el CV porque la media general es cero o no es finita.")

    # CV = sqrt(CME) / media general * 100, como porcentaje del error respecto a la media.
    return float(np.sqrt(cuadrado_medio_error) / media_general * 100)


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara tratamientos con Tukey y calcula la diferencia mínima significativa.

    Args:
        df: Datos válidos del experimento.
        col_trat: Nombre de la columna de tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Una tabla de comparaciones de Tukey y la DMS calculada.

    Raises:
        ValueError: Si alfa no está entre cero y uno.
    """
    if not 0 < alfa < 1:
        raise ValueError("El nivel alfa debe estar entre cero y uno.")

    # Tukey controla el error familiar al contrastar todas las parejas de medias.
    resultado = pairwise_tukeyhsd(
        endog=df[col_resp],
        groups=df[col_trat],
        alpha=alfa,
    )

    # Se traducen los encabezados de la salida para presentar las comparaciones.
    datos_resumen = resultado.summary().data
    comparaciones = pd.DataFrame(datos_resumen[1:], columns=datos_resumen[0])
    comparaciones = comparaciones.rename(
        columns={
            "group1": "Tratamiento 1",
            "group2": "Tratamiento 2",
            "meandiff": "Diferencia de medias",
            "p-adj": "p-valor ajustado",
            "lower": "Límite inferior",
            "upper": "Límite superior",
            "reject": "Rechaza H0",
        }
    )

    # El CME y los grados de libertad del error se obtienen del ANOVA del mismo DCA.
    anova = anova_lm(ols(f"Q({col_resp!r}) ~ C(Q({col_trat!r}))", data=df).fit(), typ=2)
    fila_error = anova.loc[anova.index.astype(str).str.lower() == "residual"].iloc[0]
    cuadrado_medio_error = float(fila_error["sum_sq"] / fila_error["df"])
    grados_libertad_error = float(fila_error["df"])

    # Para grupos balanceados r es el número común de réplicas.
    tamanos_grupo = df.groupby(col_trat, observed=True)[col_resp].count()
    tamanos = tamanos_grupo.to_numpy(dtype=float)
    numero_tratamientos = len(tamanos)
    balanceado = bool(np.all(tamanos == tamanos[0]))

    # En el desbalance se usa la media armónica de réplicas como aproximación de r.
    if balanceado:
        replicas_efectivas = float(tamanos[0])
    else:
        replicas_efectivas = float(numero_tratamientos / np.sum(1 / tamanos))
        warnings.warn(
            "El diseño está desbalanceado; la DMS calculada con la media armónica "
            "de réplicas es aproximada.",
            UserWarning,
            stacklevel=2,
        )

    # q_(1-alfa; t; glE) es el cuantil superior de rango studentizado.
    cuantil_rango = float(
        studentized_range.ppf(1 - alfa, numero_tratamientos, grados_libertad_error)
    )

    # DMS = q_(1-alfa; t; glE) * sqrt(CME / r), exacta con igual número de réplicas.
    dms = cuantil_rango * np.sqrt(cuadrado_medio_error / replicas_efectivas)
    return comparaciones, float(dms)


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la decisión de la prueba F del ANOVA de un DCA.

    Args:
        tabla: Tabla ANOVA con las columnas Fuente y p-valor.
        alfa: Nivel de significancia entre cero y uno.

    Returns:
        Explicación sencilla de la decisión sobre las medias de tratamientos.

    Raises:
        ValueError: Si alfa o la tabla no permiten tomar una decisión.
    """
    if not 0 < alfa < 1:
        raise ValueError("El nivel alfa debe estar entre cero y uno.")

    # Se localiza el p-valor de tratamientos, que contrasta la igualdad de medias.
    filas_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if filas_tratamientos.empty or not np.isfinite(float(filas_tratamientos.iloc[0])):
        raise ValueError("La tabla no contiene un p-valor válido para Tratamientos.")
    p_valor = float(filas_tratamientos.iloc[0])

    # H0: μ1 = μ2 = ... = μt; se rechaza cuando p < alfa según la prueba F.
    if p_valor < alfa:
        return (
            f"Se rechaza H0 (p = {p_valor:.4g} < alfa = {alfa:g}). "
            "Hay evidencia de que al menos dos tratamientos tienen medias distintas; "
            "se pueden revisar comparaciones múltiples para orientar la decisión."
        )
    return (
        f"No se rechaza H0 (p = {p_valor:.4g} >= alfa = {alfa:g}). "
        "Con estos datos no hay evidencia suficiente para concluir que las medias "
        "de los tratamientos sean diferentes."
    )
