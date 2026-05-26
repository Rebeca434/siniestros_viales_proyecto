"""
dashboard.py
Dashboard interactivo con Streamlit para visualizar los resultados
del análisis de siniestros viales (ATUS-INEGI).

Ejecución:
    streamlit run src/dashboard.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# ── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Siniestros Viales México",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

CARPETA_RAY = "outputs/ray"
CARPETA_SEQ = "outputs/secuencial"


# ── Carga de datos ─────────────────────────────────────────────────────────
@st.cache_data
def cargar(nombre: str, carpeta: str) -> pd.DataFrame | None:
    ruta = f"{carpeta}/{nombre}.csv"
    if os.path.exists(ruta):
        return pd.read_csv(ruta)
    return None


def cargar_todo(carpeta: str) -> dict:
    nombres = [
        "resumen_general", "por_estado", "por_municipio",
        "por_hora", "por_causa", "por_mes", "por_tipo",
        "tendencia_anual", "gravedad_por_estado",
    ]
    return {n: cargar(n, carpeta) for n in nombres}


# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.image("https://www.inegi.org.mx/contenidos/app/atencion/img/logo-inegi.png",
                 width=150)
st.sidebar.title("Siniestros Viales México")
st.sidebar.caption("Datos: ATUS — INEGI")

modo = st.sidebar.radio(
    "Fuente de resultados",
    ["Ray (distribuido)", "Secuencial (Pandas)"],
)

carpeta = CARPETA_RAY if "Ray" in modo else CARPETA_SEQ
datos   = cargar_todo(carpeta)

seccion = st.sidebar.selectbox(
    "Sección",
    ["📊 Resumen general", "🗺 Por estado", "🏙 Por municipio",
     "⏰ Por hora", "⚠️ Por causa", "📅 Por mes",
     "🚘 Por tipo de accidente", "📈 Tendencia anual",
     "⚖️ Índice de gravedad", "🏁 Benchmark de rendimiento"],
)

# ── Helpers ────────────────────────────────────────────────────────────────
PALETA = px.colors.sequential.Reds_r
COLOR1 = "#C0392B"
COLOR2 = "#E74C3C"
COLOR3 = "#F39C12"


def fig_bar(df, x, y, title, color=COLOR1, horizontal=False):
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h",
                     title=title, color_discrete_sequence=[color])
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(df, x=x, y=y, title=title,
                     color_discrete_sequence=[color])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES
# ══════════════════════════════════════════════════════════════════════════════

if "Resumen" in seccion:
    st.title("📊 Resumen General")
    df = datos.get("resumen_general")
    if df is not None and not df.empty:
        row = df.iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total accidentes",  f"{int(row['total_accidentes']):,}")
        col2.metric("Con heridos",        f"{int(row['con_heridos']):,}")
        col3.metric("Con fallecidos",     f"{int(row['con_fallecidos']):,}")
        col4.metric("Total heridos",      f"{int(row['total_heridos']):,}")
        col5.metric("Total fallecidos",   f"{int(row['total_fallecidos']):,}")
        st.info(f"Años analizados: {int(row['anio_min'])} – {int(row['anio_max'])}")
    else:
        st.warning("Ejecuta primero `python src/main.py` para generar los resultados.")

elif "estado" in seccion.lower():
    st.title("🗺 Accidentes por Estado")
    df = datos.get("por_estado")
    if df is not None:
        top = st.slider("Top estados", 5, 32, 15)
        df_top = df.head(top)
        fig = fig_bar(df_top, "entidad_nombre", "accidentes",
                      f"Top {top} estados por número de accidentes",
                      horizontal=True)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig2 = fig_bar(df_top, "entidad_nombre", "heridos",
                           "Heridos por estado", COLOR2, horizontal=True)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            fig3 = fig_bar(df_top, "entidad_nombre", "fallecidos",
                           "Fallecidos por estado", COLOR3, horizontal=True)
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Tabla completa")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin datos. Ejecuta `python src/main.py`.")

elif "municipio" in seccion.lower():
    st.title("🏙 Accidentes por Municipio (Top 50)")
    df = datos.get("por_municipio")
    if df is not None:
        estados = ["Todos"] + sorted(df["entidad_nombre"].unique().tolist())
        filtro = st.selectbox("Filtrar por estado", estados)
        df_f = df if filtro == "Todos" else df[df["entidad_nombre"] == filtro]
        fig = fig_bar(df_f.head(20), "municipio", "accidentes",
                      "Top 20 municipios con más accidentes", horizontal=True)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_f, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "hora" in seccion.lower():
    st.title("⏰ Distribución por Hora del Día")
    df = datos.get("por_hora")
    if df is not None:
        fig = px.area(df, x="hora", y="accidentes",
                      title="Accidentes por hora del día",
                      color_discrete_sequence=[COLOR1],
                      markers=True)
        fig.update_layout(xaxis=dict(dtick=1),
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        hora_pico = df.loc[df["accidentes"].idxmax(), "hora"]
        st.success(f"🕐 Hora pico: **{int(hora_pico):02d}:00 hrs** "
                   f"({int(df.loc[df['hora']==hora_pico,'accidentes'].values[0]):,} accidentes)")
    else:
        st.warning("Sin datos.")

elif "causa" in seccion.lower():
    st.title("⚠️ Causas de Accidentes")
    df = datos.get("por_causa")
    if df is not None:
        fig = px.bar(df, x="accidentes", y="causa", orientation="h",
                     title="Ranking de causas",
                     color="accidentes", color_continuous_scale="Reds")
        fig.update_layout(yaxis=dict(autorange="reversed"),
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.pie(df, values="accidentes", names="causa",
                      title="Distribución porcentual de causas",
                      color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "mes" in seccion.lower():
    st.title("📅 Tendencia Mensual")
    df = datos.get("por_mes")
    if df is not None:
        meses = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                 7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
        df["mes_nombre"] = df["mes"].map(meses)
        fig = px.line(df, x="mes_nombre", y="accidentes",
                      title="Accidentes por mes",
                      markers=True, color_discrete_sequence=[COLOR1])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "tipo" in seccion.lower():
    st.title("🚘 Tipos de Accidente")
    df = datos.get("por_tipo")
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df, x="accidentes", y="tipo_accidente", orientation="h",
                         title="Por tipo de accidente",
                         color_discrete_sequence=[COLOR1])
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.pie(df, values="accidentes", names="tipo_accidente",
                          title="Distribución (%)",
                          color_discrete_sequence=px.colors.sequential.Reds_r)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "tendencia" in seccion.lower():
    st.title("📈 Tendencia Anual")
    df = datos.get("tendencia_anual")
    if df is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["anio"], y=df["accidentes"],
                                 name="Accidentes", line=dict(color=COLOR1, width=3),
                                 mode="lines+markers"))
        fig.add_trace(go.Scatter(x=df["anio"], y=df["heridos"],
                                 name="Heridos", line=dict(color=COLOR2, width=2),
                                 mode="lines+markers"))
        fig.add_trace(go.Scatter(x=df["anio"], y=df["fallecidos"],
                                 name="Fallecidos", line=dict(color=COLOR3, width=2),
                                 mode="lines+markers"))
        fig.update_layout(title="Evolución histórica de siniestros viales",
                          xaxis_title="Año", yaxis_title="Cantidad",
                          plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "gravedad" in seccion.lower():
    st.title("⚖️ Índice de Gravedad por Estado")
    df = datos.get("gravedad_por_estado")
    if df is not None:
        st.caption("Índice = (heridos + fallecidos × 3) / accidentes")
        fig = px.bar(df.head(20), x="entidad_nombre", y="indice_gravedad",
                     title="Top 20 estados — índice de gravedad",
                     color="indice_gravedad", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["entidad_nombre", "accidentes", "heridos",
                          "fallecidos", "indice_gravedad"]], use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "benchmark" in seccion.lower():
    st.title("🏁 Benchmark de Rendimiento")

    ruta_bm = "outputs/benchmark_speedup.csv"
    if os.path.exists(ruta_bm):
        df_bm = pd.read_csv(ruta_bm)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_bm, x="modo", y="tiempo_s",
                         title="Tiempo de ejecución (segundos)",
                         color="modo",
                         color_discrete_sequence=[COLOR3, COLOR1, "#8E44AD"])
            fig.update_layout(showlegend=False,
                               plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(df_bm, x="modo", y="speedup",
                          title="Speedup vs. secuencial",
                          color="modo",
                          color_discrete_sequence=[COLOR3, COLOR1, "#8E44AD"])
            fig2.add_hline(y=1, line_dash="dash", line_color="gray",
                           annotation_text="Línea base (1×)")
            fig2.update_layout(showlegend=False,
                                plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Tabla de resultados")
        st.dataframe(df_bm, use_container_width=True)

        ruta_res = "outputs/benchmark_resultados.csv"
        if os.path.exists(ruta_res):
            st.subheader("Detalles del benchmark")
            st.dataframe(pd.read_csv(ruta_res), use_container_width=True)
    else:
        st.info("Ejecuta `python src/main.py --benchmark` para generar la comparación de rendimiento.")
        st.code("python src/main.py --benchmark", language="bash")

# ── Footer ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("Sistema distribuido para análisis de siniestros viales\n"
                   "Python · Ray · Ray Cluster · Streamlit")
