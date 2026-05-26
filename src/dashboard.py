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
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Tema terminal oscuro ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Mono', monospace !important;
    background-color: #0a0a0a !important;
    color: #e0e0e0 !important;
}

/* Fondo general */
.stApp { background-color: #0a0a0a !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0f0f0f !important;
    border-right: 1px solid #2a2a2a !important;
}
[data-testid="stSidebar"] * { font-family: 'Space Mono', monospace !important; }

/* Títulos y texto */
h1, h2, h3, h4, p, label, span, div {
    font-family: 'Space Mono', monospace !important;
    color: #e0e0e0 !important;
}
h1 { font-size: 1.1rem !important; letter-spacing: 0.12em !important;
     text-transform: uppercase !important; color: #ffffff !important;
     border-bottom: 1px solid #2a2a2a; padding-bottom: 0.5rem; }
h2 { font-size: 0.85rem !important; letter-spacing: 0.1em !important;
     text-transform: uppercase !important; color: #aaaaaa !important; }
h3 { font-size: 0.8rem !important; color: #888 !important;
     text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* Métricas */
[data-testid="stMetric"] {
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.6rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #666666 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    color: #ffffff !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* Radio y selectbox */
.stRadio label, .stSelectbox label {
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #666 !important;
}
.stRadio [data-testid="stMarkdownContainer"] p { color: #ccc !important; font-size: 0.75rem !important; }

/* Slider */
.stSlider label { font-size: 0.65rem !important; text-transform: uppercase !important;
                  letter-spacing: 0.1em !important; color: #666 !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #222 !important;
    border-radius: 2px !important;
}
.dvn-scroller { background: #0d0d0d !important; }

/* Alerts */
.stAlert { background-color: #111 !important; border: 1px solid #333 !important;
           border-radius: 2px !important; font-size: 0.75rem !important; }

/* Separadores */
hr { border-color: #1e1e1e !important; }

/* Code */
code { background-color: #1a1a1a !important; color: #a0d0a0 !important;
       font-size: 0.75rem !important; border: 1px solid #2a2a2a !important; }

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background-color: #111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 2px !important;
    color: #e0e0e0 !important;
    font-size: 0.75rem !important;
}

/* Caption */
.stCaption { color: #555 !important; font-size: 0.65rem !important;
             letter-spacing: 0.08em !important; text-transform: uppercase !important; }

/* Sidebar caption */
[data-testid="stSidebar"] .stCaption { color: #444 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 0; }
</style>
""", unsafe_allow_html=True)

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
st.sidebar.markdown("### CORE_MONITOR //")
st.sidebar.markdown("<p style='font-size:0.6rem;color:#444;letter-spacing:0.15em;text-transform:uppercase;'>SYS.01 // SINIESTROS_VIALES_MX</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr style='border-color:#1e1e1e;margin:0.5rem 0'>", unsafe_allow_html=True)

modo = st.sidebar.radio(
    "Fuente de resultados",
    ["Ray (distribuido)", "Secuencial (Pandas)"],
)

carpeta = CARPETA_RAY if "Ray" in modo else CARPETA_SEQ
datos   = cargar_todo(carpeta)

seccion = st.sidebar.selectbox(
    "Sección",
    ["Resumen general", "Por estado", "Por municipio",
     "Por hora", "Por causa", "Por mes",
     "Por tipo de accidente", "Tendencia anual",
     "Índice de gravedad", "Benchmark de rendimiento"],
)

# ── Helpers de tema ────────────────────────────────────────────────────────
BG       = "#0a0a0a"
BG2      = "#111111"
GRID     = "#1a1a1a"
COLOR1   = "#c8c8c8"   # blanco/gris principal
COLOR2   = "#888888"   # gris medio
COLOR3   = "#555555"   # gris oscuro
ACCENT   = "#ffffff"
TEXT     = "#e0e0e0"
FONT     = "Space Mono, monospace"

LAYOUT_BASE = dict(
    plot_bgcolor=BG2,
    paper_bgcolor=BG,
    font=dict(family=FONT, color=TEXT, size=11),
    title_font=dict(family=FONT, color="#666666", size=11),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=10)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=10)),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor=BG2, bordercolor=GRID, borderwidth=1, font=dict(size=10)),
)


def apply_theme(fig):
    fig.update_layout(**LAYOUT_BASE)
    return fig


def fig_bar(df, x, y, title, color=COLOR1, horizontal=False):
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h",
                     title=title, color_discrete_sequence=[color])
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig = px.bar(df, x=x, y=y, title=title,
                     color_discrete_sequence=[color])
    return apply_theme(fig)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES
# ══════════════════════════════════════════════════════════════════════════════

if "Resumen" in seccion:
    st.title("RESUMEN_GENERAL //")
    df = datos.get("resumen_general")
    if df is not None and not df.empty:
        row = df.iloc[0]
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("TOTAL_ACCIDENTES",  f"{int(row['total_accidentes']):,}")
        col2.metric("CON_HERIDOS",        f"{int(row['con_heridos']):,}")
        col3.metric("CON_FALLECIDOS",     f"{int(row['con_fallecidos']):,}")
        col4.metric("TOTAL_HERIDOS",      f"{int(row['total_heridos']):,}")
        col5.metric("TOTAL_FALLECIDOS",   f"{int(row['total_fallecidos']):,}")
        st.markdown(f"<p style='font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;margin-top:1rem;'>ANIO_RANGO // {int(row['anio_min'])} — {int(row['anio_max'])}</p>", unsafe_allow_html=True)
    else:
        st.warning("Ejecuta primero `python src/main.py` para generar los resultados.")

elif "estado" in seccion.lower():
    st.title("ACCIDENTES_BY_ESTADO //")
    df = datos.get("por_estado")
    if df is not None:
        top = st.slider("TOP_N", 5, 32, 15)
        df_top = df.head(top)
        fig = fig_bar(df_top, "entidad_nombre", "accidentes",
                      f"TOP {top} ESTADOS — ACCIDENTES",
                      horizontal=True)
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            fig2 = fig_bar(df_top, "entidad_nombre", "heridos",
                           "HERIDOS_BY_ESTADO", COLOR2, horizontal=True)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            fig3 = fig_bar(df_top, "entidad_nombre", "fallecidos",
                           "FALLECIDOS_BY_ESTADO", COLOR3, horizontal=True)
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("DATA_TABLE //")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin datos. Ejecuta `python src/main.py`.")

elif "municipio" in seccion.lower():
    st.title("ACCIDENTES_BY_MUNICIPIO //")
    df = datos.get("por_municipio")
    if df is not None:
        estados = ["Todos"] + sorted(df["entidad_nombre"].unique().tolist())
        filtro = st.selectbox("FILTER_ESTADO", estados)
        df_f = df if filtro == "Todos" else df[df["entidad_nombre"] == filtro]
        fig = fig_bar(df_f.head(20), "municipio", "accidentes",
                      "TOP 20 MUNICIPIOS — MAX_SINIESTRALIDAD", horizontal=True)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_f, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "hora" in seccion.lower():
    st.title("DELAY_TELEMETRY // HORA")
    df = datos.get("por_hora")
    if df is not None:
        hora_pico = df.loc[df["accidentes"].idxmax(), "hora"]
        n_pico    = int(df.loc[df["hora"] == hora_pico, "accidentes"].values[0])

        col1, col2 = st.columns(2)
        col1.metric("AVG_GLOBAL_HORA", f"{df['hora'].mean():.1f} HRS")
        col2.metric("MAX_DELAY_NODE",  f"{int(hora_pico):02d}:00 HRS")

        fig = px.area(df, x="hora", y="accidentes",
                      title="ACCIDENT_TIME_BY_HORA",
                      color_discrete_sequence=[COLOR1],
                      markers=True)
        fig.update_layout(xaxis=dict(dtick=1))
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"<p style='font-size:0.65rem;color:#444;letter-spacing:0.12em;text-transform:uppercase;'>HORA_PICO // {int(hora_pico):02d}:00 HRS — {n_pico:,} ACCIDENTES</p>", unsafe_allow_html=True)
    else:
        st.warning("Sin datos.")

elif "causa" in seccion.lower():
    st.title("CAUSAS_RANKING //")
    df = datos.get("por_causa")
    if df is not None:
        fig = px.bar(df, x="accidentes", y="causa", orientation="h",
                     title="FREQ_BY_CAUSA",
                     color="accidentes",
                     color_continuous_scale=[[0, "#222"], [1, "#ffffff"]])
        fig.update_layout(yaxis=dict(autorange="reversed"))
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.pie(df, values="accidentes", names="causa",
                      title="DIST_PORCENTUAL_CAUSAS",
                      color_discrete_sequence=["#fff","#ccc","#aaa","#888","#666","#444","#333","#222","#111","#0a0a0a"])
        fig2.update_traces(textfont=dict(family=FONT, color="#fff", size=10))
        apply_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "mes" in seccion.lower():
    st.title("TENDENCIA_MENSUAL //")
    df = datos.get("por_mes")
    if df is not None:
        meses = {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",
                 7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"}
        df["mes_nombre"] = df["mes"].map(meses)
        fig = px.line(df, x="mes_nombre", y="accidentes",
                      title="ACCIDENT_COUNT_BY_MES",
                      markers=True, color_discrete_sequence=[COLOR1])
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "tipo" in seccion.lower():
    st.title("TIPO_ACCIDENTE //")
    df = datos.get("por_tipo")
    if df is not None:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df, x="accidentes", y="tipo_accidente", orientation="h",
                         title="COUNT_BY_TIPO",
                         color_discrete_sequence=[COLOR1])
            fig.update_layout(yaxis=dict(autorange="reversed"))
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.pie(df, values="accidentes", names="tipo_accidente",
                          title="DIST_PCT",
                          color_discrete_sequence=["#fff","#bbb","#888","#555","#333","#1a1a1a"])
            fig2.update_traces(textfont=dict(family=FONT, color="#fff", size=10))
            apply_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "tendencia" in seccion.lower():
    st.title("TENDENCIA_ANUAL //")
    df = datos.get("tendencia_anual")
    if df is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["anio"], y=df["accidentes"],
                                 name="ACCIDENTES", line=dict(color="#ffffff", width=2),
                                 mode="lines+markers"))
        fig.add_trace(go.Scatter(x=df["anio"], y=df["heridos"],
                                 name="HERIDOS", line=dict(color="#888888", width=1, dash="dot"),
                                 mode="lines+markers"))
        fig.add_trace(go.Scatter(x=df["anio"], y=df["fallecidos"],
                                 name="FALLECIDOS", line=dict(color="#444444", width=1, dash="dash"),
                                 mode="lines+markers"))
        fig.update_layout(title="HISTORICAL_SINIESTROS_MX",
                          xaxis_title="ANIO", yaxis_title="COUNT")
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "gravedad" in seccion.lower():
    st.title("INDICE_GRAVEDAD //")
    df = datos.get("gravedad_por_estado")
    if df is not None:
        st.markdown("<p style='font-size:0.65rem;color:#444;letter-spacing:0.1em;text-transform:uppercase;'>FORMULA // (heridos + fallecidos × 3) / accidentes</p>", unsafe_allow_html=True)
        fig = px.bar(df.head(20), x="entidad_nombre", y="indice_gravedad",
                     title="TOP 20 ESTADOS — GRAVITY_INDEX",
                     color="indice_gravedad",
                     color_continuous_scale=[[0, "#1a1a1a"], [1, "#ffffff"]])
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[["entidad_nombre", "accidentes", "heridos",
                          "fallecidos", "indice_gravedad"]], use_container_width=True)
    else:
        st.warning("Sin datos.")

elif "benchmark" in seccion.lower():
    st.title("BENCHMARK_RENDIMIENTO //")

    ruta_bm = "outputs/benchmark_speedup.csv"
    if os.path.exists(ruta_bm):
        df_bm = pd.read_csv(ruta_bm)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_bm, x="modo", y="tiempo_s",
                         title="EXEC_TIME_SECONDS",
                         color="modo",
                         color_discrete_sequence=["#555555", "#aaaaaa", "#ffffff"])
            fig.update_layout(showlegend=False)
            apply_theme(fig)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(df_bm, x="modo", y="speedup",
                          title="SPEEDUP_VS_SEQUENTIAL",
                          color="modo",
                          color_discrete_sequence=["#555555", "#aaaaaa", "#ffffff"])
            fig2.add_hline(y=1, line_dash="dash", line_color="#333333",
                           annotation_text="BASELINE 1×",
                           annotation_font=dict(color="#555", size=10, family=FONT))
            fig2.update_layout(showlegend=False)
            apply_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("DATA_TABLE //")
        st.dataframe(df_bm, use_container_width=True)

        ruta_res = "outputs/benchmark_resultados.csv"
        if os.path.exists(ruta_res):
            st.subheader("BENCHMARK_DETAIL //")
            st.dataframe(pd.read_csv(ruta_res), use_container_width=True)
    else:
        st.info("Ejecuta `python src/main.py --benchmark` para generar la comparación de rendimiento.")
        st.code("python src/main.py --benchmark", language="bash")

# ── Footer ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("<hr style='border-color:#1a1a1a;margin:1rem 0'>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='font-size:0.55rem;color:#333;letter-spacing:0.1em;text-transform:uppercase;line-height:1.8;'>PYTHON · RAY · RAY_CLUSTER<br>STREAMLIT · DOCKER<br>INEGI · ATUS</p>", unsafe_allow_html=True)
