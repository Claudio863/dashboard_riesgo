# dashboard_riesgo.py  – versión con márgenes ampliados y fuentes mayores
# ────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose

from identificador_analista import dataframe_cola_aws
from lector_reporte_automático import archivo_actualizado

# ──────────────── Ajustes globales ────────────────
MAIN_TITLE_SIZE   = 32
SUBPLOT_TITLE_SZ  = 40
AXIS_LABEL_SIZE   = 22
TICK_FONT_SIZE    = 18
LEGEND_FONT_SIZE  = 18
ANALYST_TICK_SIZE = 20
MARGINS = dict(l=100, r=100, t=140, b=100)

# ──────────────── Configuración Streamlit ─────────
st.set_page_config(
    page_title="Dashboard: Resoluciones y Tendencia de Casos",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Dashboard: Resoluciones de Riesgo y Evolución de Casos")

if st.button("Actualizar Datos"):
    st.rerun()

# ──────────────── Datos ───────────────────────────
df_graf = archivo_actualizado()

unicos_graf = st.checkbox(
    "Filtrar por ruts únicos y quedarme con la fecha más actual de creación"
)


# 1) Convertir a datetime -----------------------------
df_graf["fecha_creacion"] = pd.to_datetime(
    df_graf["fecha_creacion"],   # cadenas ISO: 2025-05-21 09:03:30.591000+00:00
    utc=True,                    # reconoce el +00:00 como UTC
    errors="coerce"              # NaT si alguna cadena es inválida
)
if unicos_graf:

    df_graf = (
        df_graf
            .sort_values("fecha_creacion", ascending=False)   # más nuevos arriba
            .drop_duplicates("rut", keep="first")             # solo el registro más actual por rut
            .reset_index(drop=True)
    )
    df_cola_aws = dataframe_cola_aws()
    df_graf["rut"]       = df_graf["rut"].astype(str)
    df_cola_aws["rut"]   = df_cola_aws["rut"].astype(str)
    df_graf = df_graf.merge(
        df_cola_aws[["rut", "analista_riesgo"]], on="rut", how="left"
    )
    df_graf["analista_riesgo"].fillna("Desconocido", inplace=True)
else:
    st.info(
        "En caso de no filtrar por operación no es posible identificar "
        "el analista que realiza la evaluación."
    )

if st.checkbox("Omitir resoluciones '0' para los gráficos"):
    df_graf = df_graf[df_graf["resolucion_riesgo"] != "0"]

df_graf["fecha_creacion"] = (
    pd.to_datetime(df_graf["fecha_creacion"], errors="coerce")
      .dt.tz_localize(None)
)

# ──────────────── Filtro de fechas ────────────────
st.sidebar.header("Selecciona el intervalo de tiempo")
start_date = st.sidebar.date_input("Inicio del intervalo")
end_date   = st.sidebar.date_input("Fin del intervalo")
if not (start_date and end_date):
    st.error("Selecciona ambas fechas para continuar."); st.stop()

df_filtered = df_graf[
    (df_graf["fecha_creacion"] >= pd.to_datetime(start_date)) &
    (df_graf["fecha_creacion"] <  pd.to_datetime(end_date) + pd.Timedelta(days=1))
].copy()
df_filtered["mes"] = df_filtered["fecha_creacion"].dt.to_period("M").astype(str)
st.write(f"Mostrando datos desde **{start_date}** hasta **{end_date}**")
st.markdown(f"## {df_filtered.shape[0]} casos seleccionados en el intervalo")
# ──────────────── Parámetros comunes ──────────────
color_map = {
    "Desconocido": "#AAAAAA",
    "Aprobado": "#77DD77",
    "Aprobado con propuesta": "#FDFD96",
    "Devuelto a comercial": "#FFB347",
    "Rechazado": "#FF6961",
}
orden_categorias = list(color_map.keys())

# ──────────────── Gráfico 1  –  barras % por mes ──
show_graph1 = False
if not df_filtered.empty and df_filtered["mes"].nunique():
    df_c = (
        df_filtered.groupby(["mes", "resolucion_riesgo"])
                   .size().reset_index(name="cantidad")
    )
    tot_mes = df_filtered.groupby("mes").size().to_dict()
    df_c["porcentaje"] = df_c.apply(
        lambda r: (r["cantidad"] / tot_mes[r["mes"]]) * 100, axis=1
    )
    df_c["texto"]   = df_c["porcentaje"].round(1).astype(str) + "%"
    df_c["mes_lbl"] = df_c["mes"].map(
        lambda m: f"{m} (evaluados: {tot_mes[m]})"
    )

    fig_bar = px.bar(
        df_c,
        x="mes_lbl", y="porcentaje", text="texto",
        color="resolucion_riesgo",
        barmode="group", category_orders={"resolucion_riesgo": orden_categorias},
        color_discrete_map=color_map, template="seaborn",
    )
    fig_bar.update_traces(textposition="outside", marker_line_width=0)
    fig_bar.update_layout(
        margin=MARGINS,
        title_font_size=SUBPLOT_TITLE_SZ,
        xaxis_title="Mes",  yaxis_title="Porcentaje (%)",
        xaxis_title_font=dict(size=AXIS_LABEL_SIZE),
        yaxis_title_font=dict(size=AXIS_LABEL_SIZE),
        xaxis_tickfont=dict(size=TICK_FONT_SIZE),
        yaxis_tickfont=dict(size=TICK_FONT_SIZE),
    )
    show_graph1 = True

# ──────────────── Gráfico 2  –  torta ─────────────
sel_month = st.sidebar.selectbox("Mes para gráfico de torta",
                                 sorted(df_filtered["mes"].unique()))
show_graph2 = False
if sel_month in df_filtered["mes"].unique():
    df_pie = df_filtered[df_filtered["mes"] == sel_month]
    if not df_pie.empty:
        counts = (df_pie["resolucion_riesgo"]
                  .value_counts().reindex(orden_categorias, fill_value=0))
        if counts.sum():
            pie_trace = go.Pie(
                labels=counts.index, values=counts,
                textinfo="percent+label",
                marker=dict(colors=[color_map[k] for k in counts.index]),
            )
            show_graph2 = True

# ──────────────── Gráfico 3  –  serie de tiempo ───
show_graph3 = False
serie_raw = df_filtered.groupby(df_filtered["fecha_creacion"].dt.date).size()
if not serie_raw.empty:
    serie_raw.index = pd.to_datetime(serie_raw.index)
    serie = serie_raw.reindex(
        pd.date_range(serie_raw.index.min(), serie_raw.index.max(), freq="D"),
        fill_value=0
    )
    if len(serie) >= 8:
        trend = seasonal_decompose(serie, model="additive", period=4).trend
        df_cases = serie.reset_index().rename(columns={"index": "Fecha", 0: "Casos"})
        df_trend = trend.reset_index()
        df_trend.columns = ["Fecha", "Tendencia"]; df_trend.dropna(inplace=True)

        bar_trace = go.Bar(
            x=df_cases["Fecha"], y=df_cases["Casos"],
            name="Número de casos", opacity=0.55,
            marker=dict(color="#87CEEB"),
        )
        trend_trace = go.Scatter(
            x=df_trend["Fecha"], y=df_trend["Tendencia"],
            mode="lines+markers", name="Tendencia",
            line=dict(color="red", width=3),
        )
        show_graph3 = True

# ──────────────── Gráfico 4  –  analistas ─────────
show_graph4 = False
if unicos_graf:
    df_a = df_filtered.groupby("analista_riesgo").size().reset_index(
        name="operaciones"
    )
    if not df_a.empty and df_a["operaciones"].sum():
        fig_analista = px.bar(
            df_a, x="operaciones", y="analista_riesgo",
            text="operaciones", orientation="h", template="seaborn",
        )
        fig_analista.update_traces(textposition="outside",
                                   marker_color="#4169E1")
        fig_analista.update_layout(
            margin=MARGINS,
            xaxis_title="", yaxis_title="",
            yaxis_tickfont=dict(size=ANALYST_TICK_SIZE),
            title_font_size=SUBPLOT_TITLE_SZ,
        )
        show_graph4 = True

# ──────────────── Subplots combinados ─────────────
fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "xy"}, {"type": "xy"}],
           [{"type": "xy"}, {"type": "domain"}]],
    subplot_titles=(
        "Series de Operaciones Diarias con Tendencia",
        f"Resoluciones por mes (total: {df_filtered.shape[0]})",
        "Operaciones por Analista",
        f"Distribución de casos en {sel_month}",
    ),
)

def add_warning(fig_obj, row, col, text):
    if (row, col) == (2, 2):   # sector pie
        fig_obj.add_annotation(
            x=0.75, y=0.25, xref="paper", yref="paper",
            text=text, showarrow=False,
            font=dict(size=AXIS_LABEL_SIZE, color="red")
        )
    else:
        fig_obj.add_annotation(
            x=0.5, y=0.5, row=row, col=col,
            text=text, showarrow=False,
            font=dict(size=AXIS_LABEL_SIZE, color="red")
        )

# añade trazos o warnings
if show_graph3:
    fig.add_trace(bar_trace,   row=1, col=1)
    fig.add_trace(trend_trace, row=1, col=1)
    fig.update_xaxes(title_text="Fecha", row=1, col=1,
                     title_font=dict(size=AXIS_LABEL_SIZE),
                     tickfont=dict(size=TICK_FONT_SIZE))
    fig.update_yaxes(title_text="Número de operaciones", row=1, col=1,
                     title_font=dict(size=AXIS_LABEL_SIZE),
                     tickfont=dict(size=TICK_FONT_SIZE))
else:
    add_warning(fig, 1, 1, "No hay suficientes datos")

if show_graph1:
    for t in fig_bar.data:
        fig.add_trace(t, row=1, col=2)
    fig.update_xaxes(title_text="Mes", row=1, col=2,
                     title_font=dict(size=AXIS_LABEL_SIZE),
                     tickfont=dict(size=TICK_FONT_SIZE))
    fig.update_yaxes(title_text="Porcentaje (%)", row=1, col=2,
                     title_font=dict(size=AXIS_LABEL_SIZE),
                     tickfont=dict(size=TICK_FONT_SIZE))
else:
    add_warning(fig, 1, 2, "No hay suficientes datos")

if show_graph4:
    for t in fig_analista.data:
        fig.add_trace(t, row=2, col=1)
    fig.update_yaxes(tickfont=dict(size=ANALYST_TICK_SIZE), row=2, col=1)
else:
    add_warning(fig, 2, 1, "No disponible")

if show_graph2:
    fig.add_trace(pie_trace, row=2, col=2)
else:
    add_warning(fig, 2, 2, "No hay suficientes datos")

# Layout general
fig.update_layout(
    height=1200, margin=MARGINS,
    title_text=f"Panel de Gráficos de Evaluaciones desde {start_date} hasta {end_date} ",
    title_font_size=MAIN_TITLE_SIZE,
    font=dict(size=TICK_FONT_SIZE),
    legend_font=dict(size=LEGEND_FONT_SIZE),
)
for tr in fig.data:
    tr.showlegend = False

fig.update_layout(showlegend=False)        # respaldo por si acaso

st.plotly_chart(fig, use_container_width=True)