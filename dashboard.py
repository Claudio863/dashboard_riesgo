import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
import os
from funciones_google import login, listar_archivos_carpeta
from lector_reporte_automático import archivo_actualizado
# Configuración de la página
st.set_page_config(
    page_title="Dashboard: Resoluciones y Tendencia de Casos",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Dashboard: Resoluciones de Riesgo y Evolución de Casos")

# Botón para actualizar los datos
if st.button("Actualizar Datos"):
    st.rerun()
    #st.cache_data.clear()

df_graf = archivo_actualizado()
# Opción para filtrar por ruts únicos (última creación)
unicos_graf = st.checkbox("Filtrar por ruts únicos y quedarme con la fecha más actual de creación")
if unicos_graf:
    df_graf = df_graf.sort_values("fecha_creacion", ascending=False).drop_duplicates("rut", keep="first")
    df_graf.reset_index(drop=True, inplace=True)

# Nuevo botón para omitir registros con resolucion_riesgo == "0"
omitir_resolucion_cero = st.checkbox("Omitir resoluciones '0' para los gráficos")
if omitir_resolucion_cero:
    df_graf = df_graf[df_graf["resolucion_riesgo"] != "0"].copy()

# Convertir 'fecha_creacion' a datetime (sin zona horaria)
df_graf['fecha_creacion'] = pd.to_datetime(df_graf['fecha_creacion'], errors='coerce').dt.tz_localize(None)

# Almacenar en el estado de sesión
st.session_state['df_graf'] = df_graf

if 'df_graf' not in st.session_state:
    st.error("El DataFrame 'df_graf' no se encuentra cargado. Por favor, carga tus datos.")
    st.stop()

# ---------------------------------------------------------------------------
# Filtro de Intervalo de Tiempo (Barra lateral)
# ---------------------------------------------------------------------------
st.sidebar.header("Selecciona el intervalo de tiempo")
start_date = st.sidebar.date_input("Inicio del intervalo", key="start_date")
end_date = st.sidebar.date_input("Fin del intervalo", key="end_date")

# Validar que ambos valores estén seleccionados
if not (start_date and end_date):
    st.error("Por favor, selecciona ambos, la fecha de inicio y fin del intervalo.")
    st.stop()

st.write(f"Mostrando datos desde **{start_date}** hasta **{end_date}**")

# Filtrar el DataFrame según el intervalo seleccionado
df_filtered = df_graf[
    (df_graf['fecha_creacion'] >= pd.to_datetime(start_date)) &
    (df_graf['fecha_creacion'] < pd.to_datetime(end_date) + pd.Timedelta(days=1))
].copy()

df_filtered['mes'] = df_filtered['fecha_creacion'].dt.to_period('M').astype(str)

# ---------------------------------------------------------------------------
# Variables comunes para gráficos
# ---------------------------------------------------------------------------
# Definición de colores y orden de categorías (usado en gráfico 1 y 2)
color_map = {
    "0": "#AAAAAA",                      # gris para la categoría "0"
    "100% aprobado": "#77DD77",            # verde pastel
    "Aprobado con Propuesta": "#FDFD96",     # amarillo pastel
    "Devuelto Comercial": "#FFB347",         # naranja pastel
    "Rechazado": "#FF6961",                   # rojo pastel
}
orden_categorias = ["0", "100% aprobado", "Aprobado con Propuesta", "Devuelto Comercial", "Rechazado"]

# ---------------------------------------------------------------------------
# Gráfico 1: Barras – % de Resoluciones por Mes
# ---------------------------------------------------------------------------
if not df_filtered.empty and df_filtered['mes'].nunique() > 0:
    df_count = df_filtered.groupby(['mes', 'resolucion_riesgo']).size().reset_index(name='cantidad')
    totales_por_mes = df_filtered.groupby('mes').size().to_dict()
    # Calcular porcentaje de forma segura
    df_count['porcentaje'] = df_count.apply(
        lambda row: (row['cantidad'] / totales_por_mes.get(row['mes'], 0)) * 100
        if totales_por_mes.get(row['mes'], 0) != 0 else 0, axis=1)
    df_count['texto_porcentaje'] = df_count['porcentaje'].round(1).astype(str) + '%'
    df_count['mes_label'] = df_count['mes'].map(lambda m: f"{m} (evaluados: {totales_por_mes[m]})")

    fig_bar = px.bar(
        df_count,
        x="mes_label",
        y="porcentaje",
        color="resolucion_riesgo",
        text="texto_porcentaje",
        barmode="group",
        color_discrete_map=color_map,
        category_orders={"resolucion_riesgo": orden_categorias},
        template="seaborn",
        title=f"Resoluciones de riesgo evaluadas (total: {df_filtered.shape[0]})",
    )
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(
        xaxis_title="Mes",
        yaxis_title="Porcentaje de resoluciones (%)",
        uniformtext_minsize=14,
        uniformtext_mode='hide',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, ticksuffix="%"),
        font=dict(size=22),
        xaxis_title_font=dict(size=26),
        yaxis_title_font=dict(size=26)
    )
    show_graph1 = True
else:
    show_graph1 = False
    st.warning("No hay suficientes datos para el gráfico de Resoluciones por Mes.")

# ---------------------------------------------------------------------------
# Gráfico 2: Torta – Distribución de Resoluciones en un Mes Seleccionado
# ---------------------------------------------------------------------------
available_months = sorted(df_filtered['mes'].unique())
selected_month_for_pie = st.sidebar.selectbox("Selecciona el mes para el gráfico de torta", available_months)

if not df_filtered.empty and selected_month_for_pie in df_filtered['mes'].unique():
    df_pie = df_filtered[df_filtered['mes'] == selected_month_for_pie].copy()
    if not df_pie.empty:
        pie_counts = df_pie['resolucion_riesgo'].value_counts().reindex(orden_categorias, fill_value=0)
        if pie_counts.sum() > 0:
            pie_percentages = (pie_counts / pie_counts.sum() * 100).round(1)
            pie_trace = go.Pie(
                values=pie_percentages,
                labels=pie_percentages.index.tolist(),
                textinfo='percent+label',
                textposition='inside',
                marker=dict(colors=[color_map[label] for label in pie_percentages.index.tolist()]),
                showlegend=False
            )
            show_graph2 = True
        else:
            show_graph2 = False
            st.warning(f"No hay suficientes datos para el gráfico de torta en el mes {selected_month_for_pie}.")
    else:
        show_graph2 = False
        st.warning(f"No hay datos para el mes {selected_month_for_pie} para el gráfico de torta.")
else:
    show_graph2 = False
    st.warning(f"No hay suficientes datos para el gráfico de torta en el mes {selected_month_for_pie}.")

# ---------------------------------------------------------------------------
# Gráfico 3: Series de Tiempo – Evolución de Casos con Tendencia
# ---------------------------------------------------------------------------
serie_casos = df_filtered.groupby(df_filtered['fecha_creacion'].dt.date).size()
if not serie_casos.empty:
    serie_casos.index = pd.to_datetime(serie_casos.index)
    date_range_ts = pd.date_range(start=serie_casos.index.min(), end=serie_casos.index.max(), freq='D')
    serie_casos = serie_casos.reindex(date_range_ts, fill_value=0)
else:
    serie_casos = pd.Series(dtype=int)

# Se establece un umbral mínimo de datos para el análisis (en este caso 8 días)
if len(serie_casos) >= 8:
    result = seasonal_decompose(serie_casos, model='additive', period=4)
    tendencia = result.trend

    df_cases = serie_casos.reset_index()
    df_cases.columns = ['Fecha', 'Número de casos']
    df_trend = tendencia.reset_index()
    df_trend.columns = ['Fecha', 'Tendencia']

    bar_trace = go.Bar(
        x=df_cases['Fecha'],
        y=df_cases['Número de casos'],
        name='Número de casos',
        opacity=0.5,
        marker=dict(color="#87CEEB")
    )

    trend_trace = go.Scatter(
        x=df_trend['Fecha'],
        y=df_trend['Tendencia'],
        mode='lines+markers',
        name='Tendencia',
        line=dict(color='red', width=2)
    )
    show_graph3 = True
else:
    show_graph3 = False
    st.warning("No hay suficientes datos para el gráfico de Series de Tiempo con Tendencia.")

# ---------------------------------------------------------------------------
# Gráfico 4: Operaciones por Analista (Barras horizontales)
# ---------------------------------------------------------------------------
df_analista = df_filtered.groupby('analista_riesgo').size().reset_index(name='operaciones')
if not df_analista.empty and df_analista['operaciones'].sum() > 0:
    fig_analista = px.bar(
        df_analista,
        x='operaciones',
        y='analista_riesgo',
        text='operaciones',
        orientation='h',  # Barras horizontales
        template="seaborn",
        title=f"Operaciones por Analista (Intervalo: {start_date} - {end_date})"
    )
    fig_analista.update_traces(textposition='outside')
    fig_analista.update_layout(
        xaxis_title="",
        yaxis_title="",
        font=dict(size=22)
    )
    fig_analista.update_xaxes(showticklabels=False)
    show_graph4 = True
else:
    show_graph4 = False
    st.warning("No hay suficientes datos para el gráfico de Operaciones por Analista.")

# ---------------------------------------------------------------------------
# Crear Panel de Subgráficos Combinados
# ---------------------------------------------------------------------------
fig = make_subplots(
    rows=2, cols=2,
    specs=[[{"type": "xy"}, {"type": "domain"}],
           [{"type": "xy"}, {"type": "xy"}]],
    subplot_titles=(
        f"Resoluciones de riesgo evaluadas en producto por mes (total: {df_filtered.shape[0]})",
        f"Distribución de casos en {selected_month_for_pie}",
        "Series de Operaciones Diarias con Tendencia",
        "Operaciones por Analista"
    )
)

# Función auxiliar para agregar mensaje de advertencia en un subplot
def add_warning_annotation(fig_obj, row, col, text):
    fig_obj.add_annotation(
        x=0.5, y=0.5,
        text=text,
        showarrow=False,
        font=dict(size=20, color="red"),
        xref=f"x{'' if (row,col)==(1,1) else row}{' domain'}",  # referencia genérica
        yref=f"y{'' if (row,col)==(1,1) else row}{' domain'}",
        row=row, col=col
    )

# Subgráfico 1: Resoluciones por Mes
if show_graph1:
    for trace in fig_bar.data:
        fig.add_trace(trace, row=1, col=1)
    fig.update_xaxes(title_text="Mes", row=1, col=1)
    fig.update_yaxes(title_text="Porcentaje de resoluciones (%)", row=1, col=1)
else:
    fig.add_annotation(
        x=0.5, y=0.5,
        text="No hay suficientes datos",
        showarrow=False,
        font=dict(size=20, color="red"),
        xref="x1 domain", yref="y1 domain",
        row=1, col=1
    )

# Subgráfico 2: Torta de Distribución de Resoluciones
if show_graph2:
    fig.add_trace(pie_trace, row=1, col=2)
else:
    fig.add_annotation(
        x=0.5, y=0.5,
        text="No hay suficientes datos",
        showarrow=False,
        font=dict(size=20, color="red"),
        xref="x2 domain", yref="y2 domain",
        row=1, col=2
    )

# Subgráfico 3: Series de Tiempo – Evolución de Casos con Tendencia
if show_graph3:
    fig.add_trace(bar_trace, row=2, col=1)
    fig.add_trace(trend_trace, row=2, col=1)
    fig.update_xaxes(title_text="Fecha", row=2, col=1)
    fig.update_yaxes(title_text="Número de operaciones", row=2, col=1)
else:
    fig.add_annotation(
        x=0.5, y=0.5,
        text="No hay suficientes datos",
        showarrow=False,
        font=dict(size=20, color="red"),
        xref="x3 domain", yref="y3 domain",
        row=2, col=1
    )

# Subgráfico 4: Operaciones por Analista
if show_graph4:
    for trace in fig_analista.data:
        fig.add_trace(trace, row=2, col=2)
    fig.update_xaxes(title_text="", showticklabels=False, row=2, col=2)
    fig.update_yaxes(title_text="", row=2, col=2)
else:
    fig.add_annotation(
        x=0.5, y=0.5,
        text="No hay suficientes datos",
        showarrow=False,
        font=dict(size=20, color="red"),
        xref="x4 domain", yref="y4 domain",
        row=2, col=2
    )

fig.update_layout(
    height=1000,
    width=700,
    title_text="Panel de Gráficos de Evaluaciones",
    showlegend=False,
    font=dict(size=22)
)

# Ajustar tamaño de fuente en las anotaciones de los subplots si existen
if "annotations" in fig.layout:
    for annotation in fig.layout.annotations:
        if "font" in annotation:
            annotation.font.size += 6

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Información Adicional: Fecha de inicio de registros para operaciones por analista
# ---------------------------------------------------------------------------
if not df_filtered.empty:
    fecha_mas_antigua = df_filtered['fecha_creacion'].min()
    fecha_mas_antigua_str = fecha_mas_antigua.strftime('%Y-%m-%d')
    st.warning(f"Los registros de operaciones por analista comienzan desde **{fecha_mas_antigua_str}**")
else:
    st.warning("No hay registros en el intervalo de tiempo seleccionado.")
