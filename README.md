# Dashboard de Gestión de Riesgo

## 📋 Descripción
Sistema integral de monitoreo y gestión de datos con integración automática de Google Drive y Google Sheets, desarrollado con Streamlit.

## 🚀 Características Principales

### Gestión Automática de Google Drive
- **Detección automática diaria** a las 10:00 AM
- **Sobrescritura inteligente** de archivos (sin duplicados)
- **Manejo de errores** robusto y logging detallado
- **Interfaz simplificada** con enlaces directos a Google Drive

### Dashboard de Monitoreo de Traspaso de Producto
- **Carga automática** desde Google Sheets (ID: 1wEcS8JvfKqjHA5PlD5N6ZaixG0rFYVq_pUQK1eMz5t4)
- **Selector de mes único** con mes más reciente por defecto
- **Gráficos profesionales** optimizados para presentaciones ejecutivas
- **Métricas históricas** completas con evolución temporal
- **Análisis filtrado** por período seleccionado

## 📁 Estructura del Proyecto

```
dashboard_riesgo/
├── dashboard.py                              # Dashboard principal
├── funciones_google.py                      # Funciones de Google Drive/Sheets
├── identificador_analista.py                # Identificación de analistas
├── pages/
│   └── 2_Monitoreo_Traspaso_Producto.py    # Página de monitoreo
├── temp_archives/                           # Archivos temporales de backup
├── credentials.json                         # Credenciales de Google API
├── drive_automat.json                       # Token de Google Drive
├── requirements.txt                         # Dependencias del proyecto
└── README.md                               # Documentación
```

## 🛠️ Instalación y Configuración

### Requisitos
```bash
pip install -r requirements.txt
```

### Configuración de Google API
1. Coloca `credentials.json` en el directorio raíz
2. La primera ejecución generará `drive_automat.json` automáticamente
3. Configura los permisos necesarios para Google Drive y Google Sheets

### Ejecución
```bash
streamlit run dashboard.py
```

## 📊 Funcionalidades del Dashboard

### Página Principal (dashboard.py)
- **Estado de Google Drive** con enlaces directos
- **Sidebar simplificado** con filtros esenciales
- **Mensajes de estado** colapsables por defecto
- **Gestión automática** de archivos diarios

### Monitoreo de Traspaso de Producto
- **Métricas Históricas Ejecutivas**: KPIs principales en diseño de 4 columnas
- **Gráfico de Barras Principal**: Evolución histórica completa con línea de totales
- **Selector de Mes Único**: Análisis específico por período
- **Gráficos de Distribución**: Análisis filtrado por tipo y distribución
- **Visualizaciones Optimizadas**: Sin superposición de texto, colores corporativos

## 🎨 Características de Diseño

### Paleta de Colores Corporativa
- **Azul**: #2E86AB (Principal)
- **Magenta**: #A23B72 (Secundario)
- **Púrpura**: #8E44AD (Líneas y acentos)
- **Rojo**: #C73E1D (Alertas)

### Tipografía Profesional
- **Fuente**: Segoe UI (ejecutiva)
- **Títulos**: 24px
- **Etiquetas de ejes**: 20px
- **Texto de barras**: 16px adaptativo

### Optimizaciones de Gráficos
- **Posicionamiento adaptativo** de texto en barras pequeñas
- **Márgenes optimizados** para evitar superposición
- **Altura aumentada** (750px) para mejor legibilidad
- **Tooltips profesionales** con información detallada

## 🔄 Flujo de Trabajo Automatizado

1. **10:00 AM Diario**: Detección automática de nuevos archivos
2. **Carga de Datos**: Desde Google Sheets automáticamente
3. **Procesamiento**: Generación de métricas y visualizaciones
4. **Presentación**: Dashboard ejecutivo listo para uso

## 📈 Métricas y Análisis

### Datos Históricos Completos
- Evolución temporal de evaluaciones
- Comparativas One vs Producto
- Líneas de tendencia y totales

### Análisis Filtrado por Mes
- Resumen ejecutivo específico
- Distribución por tipo de evaluación
- Gráficos de torta optimizados

## 🔧 Mantenimiento

### Archivos de Backup
- `temp_archives/`: Contiene respaldos automáticos diarios
- Retención automática de versiones anteriores

### Logs y Monitoreo
- Logging detallado en `funciones_google.py`
- Manejo de errores con reportes claros
- Estado en tiempo real en dashboard

## 📝 Notas de Desarrollo

- **Última actualización**: Optimización completa para presentaciones ejecutivas
- **Tecnologías**: Streamlit, Google API, Plotly, Pandas
- **Compatibilidad**: Python 3.8+

---

*Dashboard desarrollado para gestión profesional de datos con integración completa de Google Workspace.*
