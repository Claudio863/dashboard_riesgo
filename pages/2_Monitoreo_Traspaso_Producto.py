import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Agregar el directorio padre al path para importar funciones
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from funciones_google import login

st.set_page_config(page_title="Monitoreo Traspaso Producto", layout="wide")

st.title("📊 Dashboard de Evaluaciones: Análisis por Tipo de Resolución")
st.markdown("---")

# ───────────────────────────────────────────
# 1. CARGA DE DATOS DESDE GOOGLE SHEETS
# ───────────────────────────────────────────

@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_datos_google_sheet():
    """Carga datos desde Google Sheet específico"""
    try:
        # ID del Google Sheet para monitoreo de traspasos
        sheet_id = '1wEcS8JvfKqjHA5PlD5N6ZaixG0rFYVq_pUQK1eMz5t4'
        
        drive = login()
        if drive is None:
            st.error("❌ No se pudo conectar a Google Drive")
            return pd.DataFrame()
            
        archivo = drive.CreateFile({'id': sheet_id})
        
        # Descargar como CSV temporal
        ruta_archivo = f'sheet_monitoreo_{sheet_id}.csv'
        archivo.GetContentFile(ruta_archivo, mimetype='text/csv')
        
        # Cargar en DataFrame
        df = pd.read_csv(ruta_archivo)
        
        # Limpiar archivo temporal
        try:
            os.remove(ruta_archivo)
        except:
            pass
            
        return df
        
    except Exception as e:
        st.error(f"Error cargando datos desde Google Sheet: {str(e)}")
        return pd.DataFrame()

# Cargar datos desde Google Sheet
with st.spinner("📊 Cargando datos desde Google Sheet..."):
    df_resoluciones = cargar_datos_google_sheet()

if not df_resoluciones.empty:
    try:
        # Verificar que el archivo tenga las columnas necesarias
        required_columns = ['username', 'name', 'count', 'mes']
        missing_columns = [col for col in required_columns if col not in df_resoluciones.columns]
        
        if missing_columns:
            st.error(f"El archivo no contiene las columnas requeridas: {missing_columns}")
            st.stop()
        
        st.success(f"✅ Datos cargados correctamente desde Google Sheet. {len(df_resoluciones)} registros encontrados.")
          # ───────────────────────────────────────────
        # 2. PREPARAR DATOS COMPLETOS (PARA EVOLUCIÓN MENSUAL)
        # ───────────────────────────────────────────
        
        # Etiqueta cada fila como Producto u One basado en username
        df_resoluciones["tipo"] = np.where(df_resoluciones["username"] == "producdigitalriesgo", 
                                          "Producto", "One")
        
        # Mapear los nombres a versiones más legibles
        mapeo_resoluciones = {
            'APROBADO_100': '100% Aprobado',
            'APROBADO_CON_PROPUESTA': 'Aprobado con Propuesta',
            'DEVUELTO_A_COMERCIAL': 'Devuelto a Comercial',
            'RECHAZADO': 'Rechazado'
        }
        df_resoluciones['name_clean'] = df_resoluciones['name'].map(mapeo_resoluciones)
        
        # Tabla completa de totales por mes y tipo (para evolución mensual)
        tabla_total_completa = (df_resoluciones.groupby(["mes", "tipo"])["count"]
                               .sum()
                               .unstack(fill_value=0)
                               .rename_axis(None))
        
        # Asegurar que existan ambas columnas
        for col in ["Producto", "One"]:
            if col not in tabla_total_completa.columns:
                tabla_total_completa[col] = 0
        
        tabla_total_completa["Total"] = tabla_total_completa["Producto"] + tabla_total_completa["One"]        # ───────────────────────────────────────────
        # 3. GRÁFICO DE EVOLUCIÓN MENSUAL (HISTÓRICO COMPLETO)
        # ───────────────────────────────────────────
        st.header("📊 Evolución Mensual: One vs Producto (Histórico Completo)")
        
        # Mostrar métricas principales del histórico completo
        total_historico_evaluaciones = tabla_total_completa['Total'].sum()
        total_historico_producto = tabla_total_completa['Producto'].sum()
        total_historico_one = tabla_total_completa['One'].sum()
        pct_historico_producto = (total_historico_producto / total_historico_evaluaciones) * 100 if total_historico_evaluaciones > 0 else 0
        
        # Métricas destacadas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📈 Total Evaluaciones Históricas", f"{total_historico_evaluaciones:,}")
        with col2:
            st.metric("🏢 Evaluaciones Producto", f"{total_historico_producto:,}", f"{pct_historico_producto:.1f}%")
        with col3:
            st.metric("🟦 Evaluaciones One", f"{total_historico_one:,}", f"{100-pct_historico_producto:.1f}%")
        with col4:
            meses_historicos = len(tabla_total_completa.index)
            st.metric("📅 Períodos Analizados", meses_historicos)
        
        st.markdown("---")
        
        # Calcular porcentajes de Producto para la línea
        porcentajes_producto = []
        for i in range(len(tabla_total_completa)):
            total = tabla_total_completa.iloc[i]["Total"]
            if total > 0:
                pct = (tabla_total_completa.iloc[i]["Producto"] / total) * 100
                porcentajes_producto.append(pct)
            else:
                porcentajes_producto.append(0)
        
        # Crear subplot con eje Y secundario
        fig_barras = make_subplots(specs=[[{"secondary_y": True}]])
          # Colores corporativos profesionales (con nuevo color para línea más visible)
        color_one = '#2E86AB'      # Azul corporativo
        color_producto = '#A23B72'  # Magenta corporativo
        color_linea = '#8E44AD'     # Púrpura vibrante (más visible que naranja)
        color_total = '#C73E1D'     # Rojo corporativo
        
        # Función para determinar posición del texto basado en tamaño de la barra
        def get_text_position_and_color(values, threshold=50):
            positions = []
            colors = []
            for val in values:
                if val < threshold:  # Barras muy pequeñas
                    positions.append('outside')
                    colors.append('#2C3E50')  # Color oscuro para texto externo
                else:  # Barras normales
                    positions.append('inside')
                    colors.append('white')  # Color blanco para texto interno
            return positions, colors
        
        # Obtener posiciones y colores para texto de One
        one_text_positions, one_text_colors = get_text_position_and_color(tabla_total_completa['One'])
        
        # Obtener posiciones y colores para texto de Producto
        producto_text_positions, producto_text_colors = get_text_position_and_color(tabla_total_completa['Producto'])
          # Crear etiquetas personalizadas para el eje X (solo mes y año)
        custom_labels = []
        for idx in tabla_total_completa.index:
            if isinstance(idx, str) and '-' in idx:
                # Formato "YYYY-MM"
                year, month = idx.split('-')
                month_names = {
                    '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
                    '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto', 
                    '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
                }
                month_name = month_names.get(month, month)
                custom_labels.append(f"{month_name} {year}")
            else:
                custom_labels.append(str(idx))
        
        # Agregar barras para One (con texto adaptativo)
        fig_barras.add_trace(
            go.Bar(
                name='One',
                x=custom_labels,  # Usar etiquetas personalizadas
                y=tabla_total_completa['One'],
                marker_color=color_one,
                marker_line=dict(width=1, color='#1C5F7A'),
                text=[f'<b>{val:,}</b>' for val in tabla_total_completa['One']],
                textposition=one_text_positions,
                textfont=dict(size=16, family="Segoe UI", color=one_text_colors, weight="bold"),  # Aumentado a 16
                opacity=0.9,
                hovertemplate='<b>One</b><br>Mes: %{x}<br>Evaluaciones: %{y:,}<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Agregar barras para Producto (con texto adaptativo)
        fig_barras.add_trace(
            go.Bar(
                name='Producto',
                x=custom_labels,  # Usar etiquetas personalizadas
                y=tabla_total_completa['Producto'],
                marker_color=color_producto,
                marker_line=dict(width=1, color='#7A2B56'),
                text=[f'<b>{val:,}</b>' for val in tabla_total_completa['Producto']],
                textposition=producto_text_positions,
                textfont=dict(size=16, family="Segoe UI", color=producto_text_colors, weight="bold"),  # Aumentado a 16
                opacity=0.9,
                hovertemplate='<b>Producto</b><br>Mes: %{x}<br>Evaluaciones: %{y:,}<extra></extra>'
            ),
            secondary_y=False
        )          # Agregar línea de totales (con texto más grande)
        fig_barras.add_trace(
            go.Scatter(
                name='Total Evaluaciones',
                x=custom_labels,  # Usar etiquetas personalizadas
                y=tabla_total_completa['Total'],
                mode='lines+markers+text',
                line=dict(color=color_total, width=3, dash='dot'),
                marker=dict(
                    size=10,  # Aumentado de 8 a 10
                    color=color_total,
                    line=dict(width=2, color='white'),
                    symbol='diamond'
                ),
                text=[f'<b>{val:,}</b>' for val in tabla_total_completa['Total']],
                textposition='top center',
                textfont=dict(size=14, family="Segoe UI", color=color_total, weight="bold"),  # Aumentado de 11 a 14
                yaxis='y',
                hovertemplate='<b>Total</b><br>Mes: %{x}<br>Evaluaciones: %{y:,}<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Agregar línea de porcentaje de Producto (nuevo color púrpura más visible)
        fig_barras.add_trace(
            go.Scatter(
                name='% Producto',
                x=custom_labels,  # Usar etiquetas personalizadas
                y=porcentajes_producto,
                mode='lines+markers+text',
                line=dict(color=color_linea, width=5, dash='solid'),  # Aumentado grosor de 4 a 5
                marker=dict(
                    size=12,  # Aumentado de 10 a 12
                    color=color_linea,
                    line=dict(width=3, color='white'),  # Aumentado borde de 2 a 3
                    symbol='circle'
                ),
                text=[f'<b>{pct:.1f}%</b>' for pct in porcentajes_producto],
                textposition='top center',
                textfont=dict(size=16, family="Segoe UI", color=color_linea, weight="bold"),  # Aumentado de 12 a 16
                yaxis='y2',
                hovertemplate='<b>% Producto</b><br>Mes: %{x}<br>Porcentaje: %{y:.1f}%<extra></extra>'
            ),
            secondary_y=True
        )          # Configurar el eje Y primario (cantidades) - ocultar números
        fig_barras.update_yaxes(
            title_text="<b>Cantidad de Evaluaciones</b>",
            title_font=dict(size=20, family="Segoe UI", color="#2C3E50"),  # Aumentado de 16 a 20
            showticklabels=False,  # Ocultar números del eje Y
            gridcolor='rgba(128,128,128,0.2)',
            gridwidth=1,
            secondary_y=False
        )
        
        # Configurar el eje Y secundario (porcentajes) - ocultar números
        fig_barras.update_yaxes(
            title_text="<b>Porcentaje Producto (%)</b>",
            title_font=dict(size=20, family="Segoe UI", color=color_linea),  # Aumentado de 16 a 20
            showticklabels=False,  # Ocultar números del eje Y
            range=[0, 100],
            gridcolor='rgba(142,68,173,0.1)',  # Actualizado color de grid al nuevo púrpura
            gridwidth=1,
            secondary_y=True
        )          # Configurar layout general con estilo corporativo y textos más grandes
        fig_barras.update_layout(
            title=dict(
                text='<b>Dashboard Ejecutivo: Evolución de Evaluaciones por Canal</b>',
                font=dict(size=24, family="Segoe UI", color="#2C3E50"),  # Aumentado de 20 a 24
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                title=dict(
                    text='<b>Período</b>',
                    font=dict(size=20, family="Segoe UI", color="#2C3E50")  # Aumentado de 16 a 20
                ),
                tickfont=dict(size=16, family="Segoe UI", color="#2C3E50"),  # Aumentado de 12 a 16
                gridcolor='rgba(128,128,128,0.2)',
                gridwidth=1,
                tickangle=45
            ),
            barmode='group',
            height=750,  # Aumentado de 700 a 750 para acomodar textos más grandes
            showlegend=True,
            legend=dict(
                font=dict(size=16, family="Segoe UI"),  # Aumentado de 14 a 16
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(128,128,128,0.3)",
                borderwidth=1
            ),            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white',
            margin=dict(l=60, r=60, t=120, b=80),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # ───────────────────────────────────────────
        # 4. SELECTOR DE MES PARA ANÁLISIS ESPECÍFICOS
        # ───────────────────────────────────────────
        st.header("📅 Análisis por Período Específico")
        
        # Obtener lista de meses disponibles
        meses_disponibles = sorted(df_resoluciones['mes'].unique())
        
        # Selector de un solo mes
        mes_seleccionado = st.selectbox(
            "Selecciona el mes para análisis detallado:",
            options=meses_disponibles,
            index=len(meses_disponibles)-1 if meses_disponibles else 0,  # Por defecto el último mes (más actual)
            help="Selecciona un mes específico para análisis de resumen ejecutivo y distribución por tipo"
        )
        
        # Filtrar datos según el mes seleccionado
        df_filtered = df_resoluciones[df_resoluciones['mes'] == mes_seleccionado].copy()        
        if df_filtered.empty:
            st.error("❌ No hay datos disponibles para el mes seleccionado.")
            st.stop()
        
        st.success(f"📊 Analizando {len(df_filtered)} registros del mes: **{mes_seleccionado}**")
          # ───────────────────────────────────────────
        # 5. PREPARAR DATOS FILTRADOS
        # ───────────────────────────────────────────
        
        # Asegurar que df_filtered tenga las columnas necesarias
        if 'tipo' not in df_filtered.columns:
            df_filtered["tipo"] = np.where(df_filtered["username"] == "producdigitalriesgo", 
                                          "Producto", "One")
        
        if 'name_clean' not in df_filtered.columns:
            df_filtered['name_clean'] = df_filtered['name'].map(mapeo_resoluciones)
        
        # Tabla de totales por mes y tipo (FILTRADOS)
        tabla_total = (df_filtered.groupby(["mes", "tipo"])["count"]
                       .sum()
                       .unstack(fill_value=0)
                       .rename_axis(None))
        
        # Asegurar que existan ambas columnas
        for col in ["Producto", "One"]:
            if col not in tabla_total.columns:
                tabla_total[col] = 0
        
        tabla_total["Total"] = tabla_total["Producto"] + tabla_total["One"]
        
        # Tabla de resoluciones por tipo (FILTRADOS)
        tabla_resoluciones_tipo = (df_filtered.groupby(["tipo", "name_clean"])["count"]
                                  .sum()
                                  .unstack(fill_value=0)
                                  .rename_axis(None))
        
        # ───────────────────────────────────────────
        # 6. MOSTRAR ESTADÍSTICAS PRINCIPALES (FILTRADAS)
        # ───────────────────────────────────────────
        st.header("📈 Resumen Ejecutivo")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_evaluaciones = tabla_total['Total'].sum()
        total_producto = tabla_total['Producto'].sum()
        total_one = tabla_total['One'].sum()
        
        with col1:
            st.metric("Total Evaluaciones", f"{total_evaluaciones:,}")
        
        with col2:
            pct_producto = (total_producto / total_evaluaciones) * 100 if total_evaluaciones > 0 else 0
            st.metric("Evaluaciones Producto", f"{total_producto:,}", f"{pct_producto:.1f}%")
        
        with col3:
            pct_one = (total_one / total_evaluaciones) * 100 if total_evaluaciones > 0 else 0
            st.metric("Evaluaciones One", f"{total_one:,}", f"{pct_one:.1f}%")
        
        with col4:
            meses_activos = len(tabla_total.index)
            st.metric("Meses Analizados", meses_activos)        # ───────────────────────────────────────────
        # 5. GRÁFICOS DE TORTA POR TIPO DE RESOLUCIÓN
        # ───────────────────────────────────────────
        st.header("🎯 Distribución por Tipo de Resolución")
        
        tipos_resolucion = tabla_resoluciones_tipo.columns
        n_cols = len(tipos_resolucion)
        
        cols = st.columns(n_cols)
        
        colores_tipo = {"One": "#FFDAB9", "Producto": "#B2F2BB"}
        
        for i, resolucion in enumerate(tipos_resolucion):
            with cols[i]:
                # Obtener datos para esta resolución
                valores = []
                labels = []
                colores = []
                
                for tipo in ["One", "Producto"]:
                    if tipo in tabla_resoluciones_tipo.index:
                        valor = tabla_resoluciones_tipo.loc[tipo, resolucion]
                        valores.append(valor)
                        labels.append(tipo)
                        colores.append(colores_tipo[tipo])
                
                total_resolucion = sum(valores)
                
                if total_resolucion > 0:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=valores,
                        marker_colors=colores,
                        textinfo='label+percent+value',
                        textfont_size=14,  # Reducido para evitar solapamiento
                        textfont_family="Arial",
                        textfont_color="black"
                    )])
                    
                    fig_pie.update_layout(
                        title=dict(
                            text=f"{resolucion}<br>Total: {total_resolucion:,}",
                            font=dict(size=16, family="Arial", color="black")
                        ),
                        height=550,  # Aumentado para más espacio
                        width=450,   # Ancho fijo para evitar solapamiento
                        showlegend=True,
                        legend=dict(
                            font=dict(size=12, family="Arial"),
                            orientation="v",  # Leyenda vertical para ahorrar espacio
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.05
                        ),
                        margin=dict(l=20, r=100, t=100, b=20)  # Márgenes amplios
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info(f"No hay datos para {resolucion}")
        
        # ───────────────────────────────────────────
        # 7. ANÁLISIS DETALLADO POR RESOLUCIÓN
        # ───────────────────────────────────────────
        st.header("🔍 Análisis Detallado por Tipo de Resolución")
        
        for resolucion in tipos_resolucion:
            with st.expander(f"📊 {resolucion}"):
                total_resolucion = tabla_resoluciones_tipo[resolucion].sum()
                porcentaje_global = (total_resolucion / df_filtered['count'].sum()) * 100
                
                st.write(f"**Total:** {total_resolucion:,} ({porcentaje_global:.1f}% del total)")
                
                col1, col2 = st.columns(2)
                
                for i, tipo in enumerate(["One", "Producto"]):
                    if tipo in tabla_resoluciones_tipo.index:
                        valor = tabla_resoluciones_tipo.loc[tipo, resolucion]
                        pct_tipo = (valor / total_resolucion) * 100 if total_resolucion > 0 else 0
                        
                        with col1 if i == 0 else col2:
                            st.metric(
                                f"{tipo}",
                                f"{valor:,}",
                                f"{pct_tipo:.1f}%"
                            )
        
        # ───────────────────────────────────────────
        # 8. DATOS RAW (OPCIONAL)
        # ───────────────────────────────────────────
        with st.expander("🗂️ Ver datos originales"):
            st.dataframe(df_filtered, use_container_width=True)
            
            # Botón para descargar
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="📥 Descargar datos procesados",
                data=csv,
                file_name="resoluciones_procesadas.csv",
                mime="text/csv"
            )        
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")
        st.info("Verifica que el Google Sheet tenga el formato correcto.")

else:
    st.info("❌ No se pudieron cargar los datos desde Google Sheet.")
    st.markdown("""
    ### Formato esperado en Google Sheet:
    - **username**: Usuario que realizó la evaluación
    - **name**: Tipo de resolución (APROBADO_100, APROBADO_CON_PROPUESTA, etc.)
    - **count**: Cantidad de evaluaciones
    - **mes**: Mes de la evaluación
    
    **ID del Google Sheet:** `1wEcS8JvfKqjHA5PlD5N6ZaixG0rFYVq_pUQK1eMz5t4`
    """)
