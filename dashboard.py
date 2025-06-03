# dashboard_riesgo.py - Nueva arquitectura con data_manager modular
# ----------------------------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
import os
from datetime import datetime, date, time
from data_manager import cargar_datos

# ------------------ Configuracion y estilos -------------------
st.set_page_config(
    page_title="Dashboard: Resoluciones y Tendencia de Casos",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #17becf);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ------------------ Constantes --------------------
MAIN_TITLE_SIZE = 28
SUBPLOT_TITLE_SZ = 24
AXIS_LABEL_SIZE = 18
TICK_FONT_SIZE = 14
LEGEND_FONT_SIZE = 16
ANALYST_TICK_SIZE = 16
MARGINS = dict(l=80, r=80, t=100, b=80)

# ------------------ Funciones auxiliares -------------------
@st.cache_data(ttl=3600)  # Cache por 1 hora
def mostrar_informacion_actualizacion():
    """Muestra información sobre el estado de actualización de datos"""
    ahora = datetime.now()
    hora_limite = time(10, 0)  # 10:00 AM
    
    if ahora.time() >= hora_limite:
        status = "🟢 Datos actualizados (después de 10:00 AM)"
    else:
        status = "🟡 Datos del día anterior (antes de 10:00 AM)"
    
    return status, ahora.strftime('%H:%M')

# ------------------ Carga de datos principal -------------------
@st.cache_data(ttl=1800)  # Cache por 30 minutos
def cargar_datos_dashboard(incluir_analistas=False):
    """Función principal para cargar datos usando el nuevo data_manager"""
    try:
        df = cargar_datos(incluir_analistas=incluir_analistas)
        if df.empty:
            st.error("❌ No se pudieron cargar los datos. Verifica la conexión con Google Drive.")
            st.stop()
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        st.stop()

# Obtener información de estado de datos
status_actualizacion, hora_actual = mostrar_informacion_actualizacion()

# ------------------ Header principal -------------------
st.markdown("""
<div class="main-header">
    <h1>🎯 Dashboard: Resoluciones de Riesgo y Evolución de Casos</h1>
</div>
""", unsafe_allow_html=True)

# ------------------ Controles principales -------------------
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 📊 Panel de Control")

with col2:
    if st.button("🔄 Actualizar Datos", type="primary"):
        st.cache_data.clear()
        st.rerun()

with col3:
    st.markdown(f"**📅 Última actualización:** {hora_actual}")
    st.markdown(f"**Status:** {status_actualizacion}")

# ------------------ Sidebar: Configuracion -------------------
st.sidebar.markdown("## ⚙️ Configuracion")

# Filtros de datos
unicos_graf = st.sidebar.checkbox(
    "🔍 Filtro resolución única más actual por cliente (ESTADO ACTUAL o FINAL del CLIENTE)",
    help="Mantiene solo el registro más reciente por RUT"
)

# Cargar datos con el nuevo sistema
with st.spinner("Cargando datos desde Google Drive..."):
    df_graf = cargar_datos_dashboard(incluir_analistas=unicos_graf)

# Procesar filtros únicos si está habilitado
if unicos_graf:
    df_graf = (
        df_graf.sort_values("fecha_creacion", ascending=False)
        .drop_duplicates("rut", keep="first")
        .reset_index(drop=True)
    )
else:
    # Si no se usa el filtro único, asegurar que la columna existe para evitar errores
    if "analista_riesgo" not in df_graf.columns:
        df_graf["analista_riesgo"] = "N/A"

# ------------------ Sidebar: Filtros de fecha -------------------
st.sidebar.markdown("## 📅 Filtros de Tiempo")

tipo_consulta = st.sidebar.radio(
    "Tipo de consulta:",
    ("📊 Intervalo de fechas", "📅 Dia especifico"),
    help="Selecciona el tipo de analisis temporal"
)

if tipo_consulta == "📊 Intervalo de fechas":
    start_date = st.sidebar.date_input("📅 Fecha inicio")
    end_date = st.sidebar.date_input("📅 Fecha fin")
    
    if not (start_date and end_date):
        st.error("⚠️ Selecciona ambas fechas para continuar")
        st.stop()
    
    # Convertir fechas a UTC para comparación
    start_datetime = pd.to_datetime(start_date).tz_localize('UTC')
    end_datetime = pd.to_datetime(end_date).tz_localize('UTC') + pd.Timedelta(days=1)
    
    df_filtered = df_graf[
        (df_graf["fecha_creacion"] >= start_datetime) &
        (df_graf["fecha_creacion"] < end_datetime)
    ].copy()
    
    intervalo_texto = f"{start_date} - {end_date}"
    
else:
    single_day = st.sidebar.date_input("📅 Selecciona el dia")
    if not single_day:
        st.error("⚠️ Selecciona un dia")
        st.stop()
      # Convertir fecha a UTC para comparación
    start_datetime = pd.to_datetime(single_day).tz_localize('UTC')
    end_datetime = start_datetime + pd.Timedelta(days=1)
    
    df_filtered = df_graf[
        (df_graf["fecha_creacion"] >= start_datetime) &
        (df_graf["fecha_creacion"] < end_datetime)
    ].copy()
    
    intervalo_texto = f"{single_day}"

# Crear campo de mes para agrupación (convertir UTC a local para display)
df_filtered["mes"] = df_filtered["fecha_creacion"].dt.tz_convert(None).dt.to_period("M").astype(str)

# ------------------ Metricas principales -------------------
if not df_filtered.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total de Casos",
            df_filtered.shape[0],
            help="Numero total de casos en el periodo seleccionado"
        )
    
    with col2:
        aprobados = len(df_filtered[df_filtered["resolucion_riesgo"].isin(["Aprobado", "100% aprobado"])])
        tasa_aprobacion = (aprobados / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        st.metric(
            "✅ Tasa de Aprobacion",
            f"{tasa_aprobacion:.1f}%",
            help="Porcentaje de casos aprobados"
        )
    
    with col3:
        if unicos_graf and "analista_riesgo" in df_filtered.columns:
            # Contar solo analistas conocidos (no "Desconocido")
            analistas_conocidos = df_filtered[df_filtered["analista_riesgo"] != "Desconocido"]
            analistas_activos = analistas_conocidos["analista_riesgo"].nunique() if not analistas_conocidos.empty else 0
            st.metric(
                "👥 Analistas Activos",
                analistas_activos,
                help="Numero de analistas que evaluaron casos"
            )
        else:
            st.metric("👥 Analistas", "N/A", help="Requiere filtro por estado actual del cliente")
    
    with col4:
        if len(df_filtered) > 0:
            periodo_dias = (df_filtered["fecha_creacion"].max() - df_filtered["fecha_creacion"].min()).days + 1
            promedio_diario = len(df_filtered) / periodo_dias if periodo_dias > 0 else 0
            st.metric(
                "📈 Promedio Diario",
                f"{promedio_diario:.1f}",
                help="Promedio de casos por dia"
            )
else:
    st.warning("⚠️ No hay datos para el periodo seleccionado")
    st.stop()

# ------------------ Configuracion de graficos -------------------
color_map = {
    "Desconocido": "#AAAAAA",
    "0": "#CCCCCC",
    "Aprobado": "#77DD77",
    "100% aprobado": "#77DD77",
    "Aprobado con propuesta": "#FDFD96",
    "Aprobado con Propuesta": "#FDFD96",
    "Devuelto a comercial": "#FFB347",
    "Devuelto Comercial": "#FFB347",
    "Rechazado": "#FF6961",
}

orden_categorias = ["0", "Aprobado", "100% aprobado", "Aprobado con propuesta", 
                   "Aprobado con Propuesta", "Devuelto a comercial", 
                   "Devuelto Comercial", "Rechazado", "Desconocido"]

# ------------------ Generacion de graficos -------------------
missing_graphs = []

# Grafico 1: Resoluciones por mes
show_graph1 = False
if not df_filtered.empty and df_filtered["mes"].nunique() > 0:
    df_c = df_filtered.groupby(["mes", "resolucion_riesgo"]).size().reset_index(name="cantidad")
    tot_mes = df_filtered.groupby("mes").size().to_dict()
    df_c["porcentaje"] = df_c.apply(
        lambda r: (r["cantidad"] / tot_mes[r["mes"]]) * 100, axis=1
    )
    df_c["texto"] = df_c["porcentaje"].round(1).astype(str) + "%"
    df_c["mes_lbl"] = df_c["mes"].map(lambda m: f"{m} ({tot_mes[m]} casos)")

    fig_bar = px.bar(
        df_c, x="mes_lbl", y="porcentaje", text="texto",
        color="resolucion_riesgo", barmode="group",
        color_discrete_map=color_map, template="plotly_white",
    )
    fig_bar.update_traces(textposition="outside", marker_line_width=0)
    fig_bar.update_layout(
        margin=MARGINS, title_font_size=SUBPLOT_TITLE_SZ,
        xaxis_title="Periodo", yaxis_title="Porcentaje (%)",
        font=dict(size=TICK_FONT_SIZE),
    )
    show_graph1 = True
else:
    missing_graphs.append("Resoluciones por Mes")

# Grafico 2: Distribucion por mes seleccionado
available_months = sorted(df_filtered["mes"].unique())
selected_month = st.sidebar.selectbox("📊 Mes para grafico circular", available_months)

show_graph2 = False
if selected_month in df_filtered["mes"].unique():
    df_pie = df_filtered[df_filtered["mes"] == selected_month]
    if not df_pie.empty:
        counts = df_pie["resolucion_riesgo"].value_counts()
        if counts.sum() > 0:
            pie_trace = go.Pie(
                labels=counts.index, values=counts,
                textinfo="percent+label", hole=0.3,
                marker=dict(colors=[color_map.get(k, "#CCCCCC") for k in counts.index]),
            )
            show_graph2 = True
        else:
            missing_graphs.append(f"Distribucion para {selected_month}")
    else:
        missing_graphs.append(f"Distribucion para {selected_month}")

# Grafico 3: Series de tiempo
show_graph3 = False
trend_trace = None
if tipo_consulta == "📅 Dia especifico":
    # Agrupar por hora
    serie_raw = df_filtered.groupby(df_filtered["fecha_creacion"].dt.hour).size()
    serie = serie_raw.reindex(range(24), fill_value=0)
    df_cases = serie.reset_index()
    df_cases.columns = ["Hora", "Casos"]
    
    bar_trace = go.Bar(
        x=df_cases["Hora"], y=df_cases["Casos"],
        name="Casos por hora", marker_color="#87CEEB",
    )
    show_graph3 = True
else:
    # Agrupar por dia
    serie_raw = df_filtered.groupby(df_filtered["fecha_creacion"].dt.date).size()
    if not serie_raw.empty:
        serie_raw.index = pd.to_datetime(serie_raw.index)
        serie = serie_raw.reindex(
            pd.date_range(serie_raw.index.min(), serie_raw.index.max(), freq="D"),
            fill_value=0
        )
        
        df_cases = serie.reset_index()
        df_cases.columns = ["Fecha", "Casos"]
        
        bar_trace = go.Bar(
            x=df_cases["Fecha"], y=df_cases["Casos"],
            name="Casos diarios", marker_color="#87CEEB", opacity=0.7,
        )
        
        # Tendencia si hay suficientes datos
        if len(serie) >= 8:
            trend = seasonal_decompose(serie, model="additive", period=4).trend
            df_trend = trend.reset_index()
            df_trend.columns = ["Fecha", "Tendencia"]
            df_trend.dropna(inplace=True)
            
            trend_trace = go.Scatter(
                x=df_trend["Fecha"], y=df_trend["Tendencia"],
                mode="lines+markers", name="Tendencia",
                line=dict(color="red", width=3),
            )
        
        show_graph3 = True

# Grafico 4: Analistas
show_graph4 = False
if unicos_graf and "analista_riesgo" in df_filtered.columns and df_filtered["analista_riesgo"].notna().any():
    # Filtrar analistas conocidos (no "Desconocido")
    df_analistas = df_filtered[df_filtered["analista_riesgo"] != "Desconocido"]
    if not df_analistas.empty:
        df_a = df_analistas.groupby("analista_riesgo").size().reset_index(name="operaciones")
        if not df_a.empty:
            fig_analista = px.bar(
                df_a, x="operaciones", y="analista_riesgo",
                text="operaciones", orientation="h", template="plotly_white",
            )
            fig_analista.update_traces(textposition="outside", marker_color="#4169E1")
            fig_analista.update_layout(
                margin=MARGINS, font=dict(size=TICK_FONT_SIZE),
                xaxis_title="", yaxis_title="",
            )
            show_graph4 = True
else:
    missing_graphs.append("Operaciones por Analista")

# ------------------ Panel de graficos combinados -------------------
st.markdown("---")
st.markdown("## 📈 Analisis Visual")

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "xy"}, {"type": "domain"}],
           [{"type": "xy"}, {"type": "xy"}]],
    subplot_titles=(
        f"📊 Resoluciones por Periodo (Total: {df_filtered.shape[0]})",
        f"🥧 Distribucion en {selected_month}",
        f"📈 Evolucion Temporal ({intervalo_texto})",
        "👥 Productividad por Analista",
    ),
)

def add_warning(fig_obj, row, col, text):
    fig_obj.add_annotation(
        x=0.5, y=0.5, row=row, col=col,
        text=f"⚠️ {text}", showarrow=False,
        font=dict(size=16, color="red")
    )

# Agregar graficos al subplot
if show_graph1:
    for t in fig_bar.data:
        fig.add_trace(t, row=1, col=1)
    fig.update_xaxes(title_text="Periodo", row=1, col=1)
    fig.update_yaxes(title_text="Porcentaje (%)", row=1, col=1)
else:
    add_warning(fig, 1, 1, "Sin datos suficientes")

if show_graph2:
    fig.add_trace(pie_trace, row=1, col=2)
else:
    add_warning(fig, 1, 2, "Sin datos para el mes")

if show_graph3:
    fig.add_trace(bar_trace, row=2, col=1)
    if trend_trace is not None:
        fig.add_trace(trend_trace, row=2, col=1)
    
    x_title = "Hora" if tipo_consulta == "📅 Dia especifico" else "Fecha"
    fig.update_xaxes(title_text=x_title, row=2, col=1)
    fig.update_yaxes(title_text="Numero de Casos", row=2, col=1)
else:
    add_warning(fig, 2, 1, "Sin datos temporales")

if show_graph4:
    for t in fig_analista.data:
        fig.add_trace(t, row=2, col=2)
    fig.update_yaxes(tickfont=dict(size=ANALYST_TICK_SIZE), row=2, col=2)
else:
    add_warning(fig, 2, 2, "Requiere filtro unico")

# Layout final
fig.update_layout(
    height=900, margin=MARGINS,
    title_text=f"📊 Dashboard de Evaluaciones - {intervalo_texto}",
    title_font_size=MAIN_TITLE_SIZE,
    font=dict(size=TICK_FONT_SIZE),
    showlegend=False, template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

# ------------------ Informacion adicional -------------------
if missing_graphs:
    st.info(f"ℹ️ Graficos no disponibles: {', '.join(missing_graphs)}")

if not df_filtered.empty:
    fecha_inicio = df_filtered["fecha_creacion"].min().strftime("%Y-%m-%d")
    st.success(f"📅 Datos disponibles desde: **{fecha_inicio}**")

# ------------------ Footer -------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🎯 Dashboard de Resoluciones de Riesgo | "
    f"Ultima actualizacion: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    "</div>",
    unsafe_allow_html=True
)
