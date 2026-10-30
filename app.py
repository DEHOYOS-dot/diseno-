import streamlit as st


AUTOR = "Escribe aquí tu nombre"

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite planear ensayos de campo de forma ordenada "
    "para comparar tratamientos, controlar fuentes de variación y obtener "
    "conclusiones sustentadas en datos; por ejemplo, al evaluar prácticas de "
    "manejo de cultivos."
)

st.header("Módulos disponibles")
modulos = [
    {
        "Módulo": "DCA — Diseño completamente al azar",
        "Cuándo se usa": "Cuando las unidades experimentales son homogéneas y los tratamientos se asignan al azar.",
        "Ejemplo agrícola": "Comparar cuatro secadores de yuca con muestras asignadas aleatoriamente.",
        "Estado": "Disponible",
    },
    {
        "Módulo": "DBCA — Diseño en bloques completos al azar",
        "Cuándo se usa": "Cuando una fuente conocida de variación permite agrupar unidades en bloques homogéneos.",
        "Ejemplo agrícola": "Comparar fertilizantes agrupando parcelas por gradiente de fertilidad del suelo.",
        "Estado": "En construcción",
    },
    {
        "Módulo": "DCL — Diseño en cuadrado latino",
        "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación mediante filas y columnas.",
        "Ejemplo agrícola": "Evaluar variedades controlando gradientes de humedad y fertilidad en el lote.",
        "Estado": "En construcción",
    },
    {
        "Módulo": "DPD — Diseño de parcelas divididas",
        "Cuándo se usa": "Cuando dos factores requieren tamaños de parcela o niveles de precisión distintos.",
        "Ejemplo agrícola": "Evaluar riego en parcelas principales y variedades en subparcelas.",
        "Estado": "En construcción",
    },
    {
        "Módulo": "Factoriales",
        "Cuándo se usa": "Cuando se estudian varios factores a la vez y se desea evaluar sus interacciones.",
        "Ejemplo agrícola": "Combinar dosis de fertilizante y densidades de siembra en un cultivo.",
        "Estado": "En construcción",
    },
    {
        "Módulo": "RSM — Metodología de superficie de respuesta",
        "Cuándo se usa": "Cuando se busca modelar y optimizar una respuesta según factores cuantitativos.",
        "Ejemplo agrícola": "Optimizar temperatura y tiempo de secado para reducir la humedad de la yuca.",
        "Estado": "En construcción",
    },
]
st.dataframe(modulos, width="stretch", hide_index=True)

st.header("Cómo usar la aplicación")
st.markdown(
    """
1. Elige un módulo en el menú lateral.
2. Carga o revisa los datos requeridos por el módulo.
3. Revisa los resultados y su interpretación.
4. Verifica los resultados a mano y contrástalos con los supuestos del diseño.
"""
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.header("Información del estudiante")
    st.write(f"**Autor:** {AUTOR}")
    st.write("**Curso:** Diseño Experimental")
    st.write("**Semestre:** 2026-2")
