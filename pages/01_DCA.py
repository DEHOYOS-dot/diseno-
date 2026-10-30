"""Interfaz de análisis para un diseño completamente al azar."""

import io
from pathlib import Path
import warnings

import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.stats import f

from utils.anova_utils import (
    ajustar_dca,
    cargar_datos,
    coeficiente_variacion,
    interpretar_dca,
    resumen_tratamientos,
    tabla_anova,
    tukey,
    validar_dca,
)
from utils.diagnostico_utils import (
    grafico_qq,
    grafico_residuos_vs_ajustados,
    prueba_levene,
    prueba_shapiro,
    residuos_y_ajustados,
)


@st.cache_data
def cargar_archivo(nombre: str, contenido: bytes | None) -> pd.DataFrame:
    """Carga y almacena en caché un CSV o Excel.

    Args:
        nombre: Nombre del archivo; se usa su extensión para identificar el formato.
        contenido: Bytes del archivo cargado, o ``None`` para leer la ruta recibida.

    Returns:
        Datos leídos mediante la función común de carga.
    """
    # El archivo predeterminado se lee desde la carpeta de datos del repositorio.
    if contenido is None:
        return cargar_datos(nombre)

    # El nombre adjunto permite que cargar_datos identifique CSV o Excel en memoria.
    archivo = io.BytesIO(contenido)
    archivo.name = nombre
    return cargar_datos(archivo)


st.title("DCA — Diseño completamente al azar")
st.write(
    "El diseño completamente al azar compara tratamientos asignados al azar "
    "a unidades experimentales homogéneas. En este ejemplo se evalúa la humedad "
    "final de yuca (%) obtenida con cuatro secadores solares, con cuatro réplicas "
    "por secador."
)

archivo_cargado = st.file_uploader(
    "Carga los datos del experimento",
    type=["csv", "xlsx"],
)

if archivo_cargado is None:
    ruta_ejemplo = Path(__file__).resolve().parents[1] / "data" / "dca_secadores.csv"
    st.caption(
        "No se cargó un archivo; se usan los datos de ejemplo "
        "`data/dca_secadores.csv`."
    )
    nombre_archivo = str(ruta_ejemplo)
    contenido_archivo = None
else:
    nombre_archivo = archivo_cargado.name
    contenido_archivo = archivo_cargado.getvalue()

try:
    datos = cargar_archivo(nombre_archivo, contenido_archivo)
except (ImportError, OSError, ValueError) as error:
    st.error(f"No se pudo cargar el archivo: {error}")
    st.stop()

if datos.empty or len(datos.columns) == 0:
    st.error("El archivo no contiene datos ni columnas para analizar.")
    st.stop()

columnas = [str(columna) for columna in datos.columns]
columnas_numericas = [
    columna
    for columna in datos.columns
    if pd.api.types.is_numeric_dtype(datos[columna])
    and not pd.api.types.is_bool_dtype(datos[columna])
]
columnas_respuesta = [
    columna
    for columna in columnas_numericas
    if not any(
        identificador in str(columna).casefold()
        for identificador in ("id", "rep", "réplica", "repetición")
    )
]
if not columnas_respuesta:
    columnas_respuesta = columnas_numericas
columna_tratamiento_inicial = next(
    (
        str(columna)
        for columna in datos.columns
        if not pd.api.types.is_numeric_dtype(datos[columna])
    ),
    columnas[0],
)
columna_respuesta_inicial = next(
    (
        str(columna)
        for columna in columnas_respuesta
        if str(columna) != columna_tratamiento_inicial
    ),
    next(
        (columna for columna in columnas if columna != columna_tratamiento_inicial),
        columnas[0],
    ),
)

col_trat, col_resp = st.columns(2)
with col_trat:
    columna_tratamiento = st.selectbox(
        "Columna de tratamiento",
        options=columnas,
        index=columnas.index(columna_tratamiento_inicial),
    )
with col_resp:
    columna_respuesta = st.selectbox(
        "Columna de respuesta",
        options=columnas,
        index=columnas.index(columna_respuesta_inicial),
    )

alfa = st.slider(
    "Nivel de significancia (α)",
    min_value=0.01,
    max_value=0.10,
    value=0.05,
    step=0.01,
    format="%.2f",
)

errores = validar_dca(datos, columna_tratamiento, columna_respuesta)
if errores:
    for error in errores:
        st.error(error)
    st.stop()

modelo = ajustar_dca(datos, columna_tratamiento, columna_respuesta)
anova = tabla_anova(modelo)
resumen = resumen_tratamientos(datos, columna_tratamiento, columna_respuesta)
fila_tratamientos = anova.loc[anova["Fuente"] == "Tratamientos"].iloc[0]
fila_error = anova.loc[anova["Fuente"] == "Error"].iloc[0]
significativo = float(fila_tratamientos["p-valor"]) < alfa

pestana_datos, pestana_anova, pestana_comparaciones, pestana_graficos, pestana_supuestos = st.tabs(
    ["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"]
)

with pestana_datos:
    st.subheader("Datos del experimento")
    st.dataframe(datos, width="stretch", hide_index=True)
    st.subheader("Resumen por tratamiento")
    st.dataframe(resumen, width="stretch", hide_index=True)

with pestana_anova:
    st.subheader("Tabla de análisis de varianza")
    st.dataframe(
        anova.style.format(
            {columna: "{:.4f}" for columna in ("gl", "SC", "CM", "F", "p-valor")},
            na_rep="—",
        ),
        width="stretch",
        hide_index=True,
    )
    grados_libertad_tratamientos = int(fila_tratamientos["gl"])
    grados_libertad_error = int(fila_error["gl"])
    f_critica = float(
        f.ppf(1 - alfa, grados_libertad_tratamientos, grados_libertad_error)
    )
    st.metric("F crítica", f"{f_critica:.4f}")
    st.metric(
        "Coeficiente de variación (CV)",
        f"{coeficiente_variacion(modelo, datos, columna_respuesta):.4f} %",
    )
    interpretacion = interpretar_dca(anova, alfa)
    if significativo:
        st.success(interpretacion)
    else:
        st.info(interpretacion)

with pestana_comparaciones:
    st.subheader("Comparaciones múltiples de Tukey")
    if significativo:
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            comparaciones, dms = tukey(
                datos,
                columna_tratamiento,
                columna_respuesta,
                alfa,
            )
        for aviso in avisos:
            st.warning(str(aviso.message))
        st.dataframe(comparaciones, width="stretch", hide_index=True)
        st.metric("Diferencia mínima significativa (DMS)", f"{dms:.4f}")
    else:
        st.info(
            "No se realiza la prueba de Tukey porque el ANOVA no detectó "
            "diferencias estadísticamente significativas entre tratamientos "
            f"con α = {alfa:.2f}."
        )

with pestana_graficos:
    st.subheader("Distribución de la respuesta por tratamiento")
    grafico_cajas = px.box(
        datos,
        x=columna_tratamiento,
        y=columna_respuesta,
        points="all",
        title="Respuesta por tratamiento",
        labels={
            columna_tratamiento: "Tratamiento",
            columna_respuesta: "Respuesta",
        },
    )
    st.plotly_chart(grafico_cajas, width="stretch")

    st.subheader("Media de la respuesta por tratamiento")
    grafico_medias = px.bar(
        resumen,
        x=columna_tratamiento,
        y="media",
        error_y="desviación estándar",
        text_auto=".2f",
        title="Media por tratamiento",
        labels={
            columna_tratamiento: "Tratamiento",
            "media": "Media de la respuesta",
            "desviación estándar": "Desviación estándar",
        },
    )
    st.plotly_chart(grafico_medias, width="stretch")

with pestana_supuestos:
    st.subheader("Diagnóstico de supuestos del DCA")
    st.write(
        "**Normalidad:** Shapiro-Wilk y el gráfico Q-Q revisan si los residuos "
        "son compatibles con una distribución normal."
    )
    st.write(
        "**Homogeneidad de varianzas:** Levene, centrada en las medianas, evalúa "
        "si la variabilidad de la respuesta es similar entre tratamientos."
    )
    st.write(
        "**Independencia:** no se determina con una prueba de estos datos; se "
        "respalda principalmente con la asignación aleatoria de los tratamientos "
        "y la ejecución independiente de las unidades experimentales."
    )

    diagnostico = residuos_y_ajustados(modelo)
    shapiro_estadistico, shapiro_p, shapiro_conclusion = prueba_shapiro(
        diagnostico["Residuos"], alfa
    )
    levene_estadistico, levene_p, levene_conclusion = prueba_levene(
        datos,
        columna_tratamiento,
        columna_respuesta,
        alfa,
    )
    tabla_supuestos = pd.DataFrame(
        [
            {
                "Prueba": "Shapiro-Wilk",
                "Supuesto": "Normalidad de los residuos",
                "Estadístico": shapiro_estadistico,
                "p-valor": shapiro_p,
                "Conclusión": shapiro_conclusion,
            },
            {
                "Prueba": "Levene (mediana)",
                "Supuesto": "Homogeneidad de varianzas",
                "Estadístico": levene_estadistico,
                "p-valor": levene_p,
                "Conclusión": levene_conclusion,
            },
        ]
    )
    st.dataframe(
        tabla_supuestos.style.format(
            {"Estadístico": "{:.4f}", "p-valor": "{:.4f}"}
        ),
        width="stretch",
        hide_index=True,
    )

    col_grafico_residuos, col_grafico_qq = st.columns(2)
    with col_grafico_residuos:
        st.plotly_chart(
            grafico_residuos_vs_ajustados(diagnostico),
            width="stretch",
        )
    with col_grafico_qq:
        st.plotly_chart(grafico_qq(diagnostico["Residuos"]), width="stretch")
