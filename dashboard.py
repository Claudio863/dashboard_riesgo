# dashboard_riesgo.py  – versión con márgenes ampliados y fuentes mayores
# ────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
import os
from datetime import datetime, date
from funciones_google import login, listar_archivos_carpeta
from identificador_analista import dataframe_cola_aws
from lector_reporte_automático import archivo_actualizado

# ──────────────── Configuración y estilos ─────────────────
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

# ──────────────── Constantes ────────────────
MAIN_TITLE_SIZE = 28
SUBPLOT_TITLE_SZ = 24
AXIS_LABEL_SIZE = 18
TICK_FONT_SIZE = 14
LEGEND_FONT_SIZE = 16
ANALYST_TICK_SIZE = 16
MARGINS = dict(l=80, r=80, t=100, b=80)

FOLDER_ID = "1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"
CACHE_FILE = "datos_diarios_cache.csv"

# ──────────────── Funciones auxiliares ─────────────────
@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_google_sheet_en_dataframe(sheet_id, ruta_descarga=""):
    """Carga un Google Sheet específico en DataFrame"""
    drive = login()
    archivo = drive.CreateFile({'id': sheet_id})
    ruta_archivo = os.path.join(ruta_descarga, f'sheet_{sheet_id}.csv')
    archivo.GetContentFile(ruta_archivo, mimetype='text/csv')
    df = pd.read_csv(ruta_archivo)
    return df

def obtener_datos_google_sheets():
    """Obtiene datos combinados de ambos Google Sheets"""
    sheet_id1 = '1rmSOvyghKM5WpDESHOEnRvVAgtMhELnjys6V9cZ9MG0'
    sheet_id2 = '10_ngye6Gevc44m-D2RI2pnpcrVarjXoMrFoYowrTWj4'
    
    df1 = cargar_google_sheet_en_dataframe(sheet_id1)
    df2 = cargar_google_sheet_en_dataframe(sheet_id2)
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Procesar datos
    df_procesado = df[["full_name", "resolucion_riesgo", "fecha_creacion", "analista_riesgo"]].dropna()
    df_procesado.reset_index(drop=True, inplace=True)
    df_procesado["rut"] = df_procesado["full_name"].apply(lambda x: x.split("_")[0])
    
    return df_procesado

def verificar_y_obtener_datos_del_dia():
    """Verifica si existen datos del día actual, si no los descarga"""
    hoy = date.today().strftime("%Y-%m-%d")
    archivo_cache_hoy = f"datos_{hoy}.csv"
    
    if os.path.exists(archivo_cache_hoy):
        # Cargar datos del cache
        return pd.read_csv(archivo_cache_hoy)
    else:
        # Descargar nuevos datos
        with st.spinner("Descargando datos actualizados de Google Sheets..."):
            df_hoy = obtener_datos_google_sheets()
            # Guardar cache
            df_hoy.to_csv(archivo_cache_hoy, index=False)
            # Limpiar archivos antiguos
            for archivo in os.listdir("."):
                if archivo.startswith("datos_") and archivo.endswith(".csv") and archivo != archivo_cache_hoy:
                    try:
                        os.remove(archivo)
                    except:
                        pass
        return df_hoy

def obtener_datos_combinados():
    """Combina datos históricos con datos actuales de Google Sheets"""
    # Datos del día actual desde Google Sheets
    df_actual = verificar_y_obtener_datos_del_dia()
    df_actual['fecha_creacion'] = pd.to_datetime(df_actual['fecha_creacion'], errors='coerce').dt.tz_localize(None)

    # Datos históricos desde archivo
    df_historico = archivo_actualizado()
    # --- Validación defensiva ---
    if "fecha_creacion" not in df_historico.columns:
        st.error(
            "❌ El archivo histórico cargado no contiene la columna 'fecha_creacion'. "
            "Verifica que el respaldo tenga la estructura correcta o vuelve a generar el archivo."
        )
        st.stop()
    # --- Fin validación ---
    df_historico["fecha_creacion"] = pd.to_datetime(
        df_historico["fecha_creacion"], utc=True, errors="coerce"
    ).dt.tz_localize(None)

    # Filtrar datos históricos para evitar duplicados (excluir hoy)
    hoy = pd.Timestamp.now().normalize()
    df_historico = df_historico[df_historico['fecha_creacion'] < hoy]

    # Combinar datasets
    df_final = pd.concat([df_historico, df_actual], ignore_index=True)
    
    return df_final

# ──────────────── Header principal ─────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 Dashboard: Resoluciones de Riesgo y Evolución de Casos</h1>
</div>
""", unsafe_allow_html=True)

# ──────────────── Controles principales ─────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### 📊 Panel de Control")

with col2:
    if st.button("🔄 Actualizar Datos", type="primary"):
        st.cache_data.clear()
        st.rerun()

with col3:
    st.markdown(f"**📅 Última actualización:** {datetime.now().strftime('%H:%M')}")

# ──────────────── Carga de datos ─────────────────
@st.cache_data(ttl=1800)  # Cache por 30 minutos
def cargar_datos():
    return obtener_datos_combinados()

df_graf = cargar_datos()

# ──────────────── Sidebar: Configuración ─────────────────
st.sidebar.markdown("## ⚙️ Configuración")

# Filtros de datos
unicos_graf = st.sidebar.checkbox(
    "🔍 Filtrar por ruts únicos (fecha más reciente)",
    help="Mantiene solo el registro más reciente por RUT"
)

omitir_cero = st.sidebar.checkbox(
    "🚫 Omitir resoluciones '0'",
    help="Excluye resoluciones con valor '0' de los gráficos"
)

# Procesar filtros
if unicos_graf:
    df_graf = (
        df_graf.sort_values("fecha_creacion", ascending=False)
        .drop_duplicates("rut", keep="first")
        .reset_index(drop=True)
    )
    
    # Agregar información de analistas
    df_cola_aws = dataframe_cola_aws()
    df_graf["rut"] = df_graf["rut"].astype(str)
    df_cola_aws["rut"] = df_cola_aws["rut"].astype(str)
    df_graf = df_graf.merge(
        df_cola_aws[["rut", "analista_riesgo"]], on="rut", how="left"
    )
    df_graf["analista_riesgo"].fillna("Desconocido", inplace=True)

if omitir_cero:
    df_graf = df_graf[df_graf["resolucion_riesgo"] != "0"]

# ──────────────── Sidebar: Filtros de fecha ─────────────────
st.sidebar.markdown("## 📅 Filtros de Tiempo")

tipo_consulta = st.sidebar.radio(
    "Tipo de consulta:",
    ("📊 Intervalo de fechas", "📅 Día específico"),
    help="Selecciona el tipo de análisis temporal"
)

if tipo_consulta == "📊 Intervalo de fechas":
    start_date = st.sidebar.date_input("📅 Fecha inicio")
    end_date = st.sidebar.date_input("📅 Fecha fin")
    
    if not (start_date and end_date):
        st.error("⚠️ Selecciona ambas fechas para continuar")
        st.stop()
    
    df_filtered = df_graf[
        (df_graf["fecha_creacion"] >= pd.to_datetime(start_date)) &
        (df_graf["fecha_creacion"] < pd.to_datetime(end_date) + pd.Timedelta(days=1))
    ].copy()
    
    intervalo_texto = f"{start_date} - {end_date}"
    
else:
    single_day = st.sidebar.date_input("📅 Selecciona el día")
    if not single_day:
        st.error("⚠️ Selecciona un día")
        st.stop()
    
    df_filtered = df_graf[
        (df_graf["fecha_creacion"] >= pd.to_datetime(single_day)) &
        (df_graf["fecha_creacion"] < pd.to_datetime(single_day) + pd.Timedelta(days=1))
    ].copy()
    
    intervalo_texto = f"{single_day}"

df_filtered["mes"] = df_filtered["fecha_creacion"].dt.to_period("M").astype(str)

# ──────────────── Métricas principales ─────────────────
if not df_filtered.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📊 Total de Casos",
            df_filtered.shape[0],
            help="Número total de casos en el período seleccionado"
        )
    
    with col2:
        aprobados = len(df_filtered[df_filtered["resolucion_riesgo"].isin(["Aprobado", "100% aprobado"])])
        tasa_aprobacion = (aprobados / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        st.metric(
            "✅ Tasa de Aprobación",
            f"{tasa_aprobacion:.1f}%",
            help="Porcentaje de casos aprobados"
        )
    
    with col3:
        if unicos_graf and "analista_riesgo" in df_filtered.columns:
            analistas_activos = df_filtered["analista_riesgo"].nunique()
            st.metric(
                "👥 Analistas Activos",
                analistas_activos,
                help="Número de analistas que evaluaron casos"
            )
        else:
            st.metric("👥 Analistas", "N/A", help="Requiere filtro por RUT único")
    
    with col4:
        if len(df_filtered) > 0:
            periodo_dias = (df_filtered["fecha_creacion"].max() - df_filtered["fecha_creacion"].min()).days + 1
            promedio_diario = len(df_filtered) / periodo_dias if periodo_dias > 0 else 0
            st.metric(
                "📈 Promedio Diario",
                f"{promedio_diario:.1f}",
                help="Promedio de casos por día"
            )
else:
    st.warning("⚠️ No hay datos para el período seleccionado")
    st.stop()

# ──────────────── Configuración de gráficos ─────────────────
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

# ──────────────── Generación de gráficos ─────────────────
missing_graphs = []

# Gráfico 1: Resoluciones por mes
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
        xaxis_title="Período", yaxis_title="Porcentaje (%)",
        font=dict(size=TICK_FONT_SIZE),
    )
    show_graph1 = True
else:
    missing_graphs.append("Resoluciones por Mes")

# Gráfico 2: Distribución por mes seleccionado
available_months = sorted(df_filtered["mes"].unique())
selected_month = st.sidebar.selectbox("📊 Mes para gráfico circular", available_months)

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
            missing_graphs.append(f"Distribución para {selected_month}")
    else:
        missing_graphs.append(f"Distribución para {selected_month}")

# Gráfico 3: Series de tiempo
show_graph3 = False
trend_trace = None
if tipo_consulta == "📅 Día específico":
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
    # Agrupar por día
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

# Gráfico 4: Analistas
show_graph4 = False
if unicos_graf and "analista_riesgo" in df_filtered.columns:
    df_a = df_filtered.groupby("analista_riesgo").size().reset_index(name="operaciones")
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

# ──────────────── Panel de gráficos combinados ─────────────────
st.markdown("---")
st.markdown("## 📈 Análisis Visual")

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "xy"}, {"type": "domain"}],
           [{"type": "xy"}, {"type": "xy"}]],
    subplot_titles=(
        f"📊 Resoluciones por Período (Total: {df_filtered.shape[0]})",
        f"🥧 Distribución en {selected_month}",
        f"📈 Evolución Temporal ({intervalo_texto})",
        "👥 Productividad por Analista",
    ),
)

def add_warning(fig_obj, row, col, text):
    fig_obj.add_annotation(
        x=0.5, y=0.5, row=row, col=col,
        text=f"⚠️ {text}", showarrow=False,
        font=dict(size=16, color="red")
    )

# Agregar gráficos al subplot
if show_graph1:
    for t in fig_bar.data:
        fig.add_trace(t, row=1, col=1)
    fig.update_xaxes(title_text="Período", row=1, col=1)
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
    
    x_title = "Hora" if tipo_consulta == "📅 Día específico" else "Fecha"
    fig.update_xaxes(title_text=x_title, row=2, col=1)
    fig.update_yaxes(title_text="Número de Casos", row=2, col=1)
else:
    add_warning(fig, 2, 1, "Sin datos temporales")

if show_graph4:
    for t in fig_analista.data:
        fig.add_trace(t, row=2, col=2)
    fig.update_yaxes(tickfont=dict(size=ANALYST_TICK_SIZE), row=2, col=2)
else:
    add_warning(fig, 2, 2, "Requiere filtro único")

# Layout final
fig.update_layout(
    height=900, margin=MARGINS,
    title_text=f"📊 Dashboard de Evaluaciones - {intervalo_texto}",
    title_font_size=MAIN_TITLE_SIZE,
    font=dict(size=TICK_FONT_SIZE),
    showlegend=False, template="plotly_white",
)

st.plotly_chart(fig, use_container_width=True)

# ──────────────── Información adicional ─────────────────
if missing_graphs:
    st.info(f"ℹ️ Gráficos no disponibles: {', '.join(missing_graphs)}")

if not df_filtered.empty:
    fecha_inicio = df_filtered["fecha_creacion"].min().strftime("%Y-%m-%d")
    st.success(f"📅 Datos disponibles desde: **{fecha_inicio}**")

# ──────────────── Footer ─────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🎯 Dashboard de Resoluciones de Riesgo | "
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    "</div>",
    unsafe_allow_html=True
)