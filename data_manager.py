"""
Módulo para gestión de datos del dashboard de riesgo
Maneja la descarga, actualización y procesamiento de datos desde Google Drive
"""

import pandas as pd
import os
from datetime import date, datetime, time
from funciones_google import login, listar_archivos_carpeta, bajar_archivo_por_id

# Configuración de IDs
ID_CARPETA_RAIZ = "1KRTHc_bOSF4WxX_RIXVpa2_kaypxMMYP"
ID_CARPETA_ACTUALIZADOS = "1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"
RUTA_TEMP = "temp_archives"

# IDs de Google Sheets para analistas
SHEET_ID_ANALISTAS_1 = '1rmSOvyghKM5WpDESHOEnRvVAgtMhELnjys6V9cZ9MG0'
SHEET_ID_ANALISTAS_2 = '10_ngye6Gevc44m-D2RI2pnpcrVarjXoMrFoYowrTWj4'

def obtener_fecha_actual():
    """Obtiene año y mes actual en formato requerido"""
    hoy = date.today()
    anio_actual = str(hoy.year)
    mes_actual = f"{hoy.month:02d}"  # Formato con 0 inicial si es necesario
    return anio_actual, mes_actual

def obtener_archivo_mas_reciente():
    """
    Navega por la estructura de carpetas en Drive para obtener 
    el archivo manual_evaluation más reciente
    """
    anio_actual, mes_actual = obtener_fecha_actual()
    
    try:
        # Navegar por carpeta raíz -> año -> mes
        carp_raiz = listar_archivos_carpeta(ID_CARPETA_RAIZ)
        anio = carp_raiz[carp_raiz["Nombre"] == anio_actual]
        
        if anio.empty:
            raise ValueError(f"No se encontró la carpeta del año {anio_actual}")
        
        carp_anio = listar_archivos_carpeta(anio["ID"].values[0])
        mes = carp_anio[carp_anio["Nombre"] == mes_actual]
        
        if mes.empty:
            raise ValueError(f"No se encontró la carpeta del mes {mes_actual}")
        
        carp_mes = listar_archivos_carpeta(mes["ID"].values[0])
        
        # Procesar fechas y filtrar CSV
        carp_mes["Fecha Creación"] = pd.to_datetime(
            carp_mes["Fecha Creación"],
            utc=True,
            errors="coerce"
        )
        
        # Ordenar por fecha más reciente y filtrar CSV
        carp_mes = (
            carp_mes
            .sort_values("Fecha Creación", ascending=False)
            .reset_index(drop=True)
        )
        carp_mes = carp_mes[carp_mes["Tipo"] == "text/csv"]
        
        if carp_mes.empty:
            raise ValueError("No se encontraron archivos CSV en la carpeta del mes")
        
        return carp_mes.iloc[0]
        
    except Exception as e:
        print(f"Error al obtener archivo más reciente: {e}")
        return None

def verificar_necesidad_actualizacion():
    """
    Verifica si es necesario actualizar el archivo basado en:
    1. Si existe un archivo actualizado del día actual
    2. Si es después de las 10:00 AM
    """
    hoy = date.today()
    ahora = datetime.now().time()
    hora_limite = time(10, 0)  # 10:00 AM
    
    try:
        # Verificar archivo en carpeta de actualizados
        archivos_actualizados = listar_archivos_carpeta(ID_CARPETA_ACTUALIZADOS)
        
        # Buscar archivo del día actual
        for _, archivo in archivos_actualizados.iterrows():
            fecha_archivo = pd.to_datetime(archivo["Fecha Creación"], utc=True).date()
            if fecha_archivo == hoy:
                # Si existe archivo del día actual y es después de las 10 AM, no actualizar
                if ahora >= hora_limite:
                    return False, archivo
                else:
                    # Es muy temprano, usar archivo existente
                    return False, archivo
        
        # No existe archivo del día actual, necesita actualización
        return True, None
        
    except Exception as e:
        print(f"Error al verificar necesidad de actualización: {e}")
        return True, None

def cargar_google_sheet_analistas(sheet_id, ruta_descarga="."):
    """Carga un Google Sheet específico con datos de analistas"""
    try:
        drive = login()
        archivo = drive.CreateFile({'id': sheet_id})
        
        ruta_archivo = os.path.join(ruta_descarga, f'analistas_{sheet_id}.csv')
        archivo.GetContentFile(ruta_archivo, mimetype='text/csv')
        
        df = pd.read_csv(ruta_archivo)
        return df
    except Exception as e:
        print(f"Error al cargar Google Sheet {sheet_id}: {e}")
        return pd.DataFrame()

def obtener_datos_analistas():
    """
    Combina datos de analistas de ambos Google Sheets y procesa
    para obtener la asignación más reciente por RUT
    """
    try:
        # Cargar ambos sheets
        df1 = cargar_google_sheet_analistas(SHEET_ID_ANALISTAS_1)
        df2 = cargar_google_sheet_analistas(SHEET_ID_ANALISTAS_2)
        
        if df1.empty and df2.empty:
            return pd.DataFrame()
        
        # Combinar DataFrames
        df = pd.concat([df1, df2], ignore_index=True)
        
        if df.empty:
            return pd.DataFrame()
        
        # Procesar datos
        df["rut"] = df["full_name"].str.partition("_")[0]
        df = df.drop_duplicates(subset="full_name").copy()
        df.reset_index(drop=True, inplace=True)
        
        # Procesar fechas
        df["fecha_creacion"] = pd.to_datetime(
            df["fecha_creacion"],
            utc=True,
            errors="coerce"
        )
        
        # Obtener registro más reciente por RUT
        df = (
            df
            .sort_values("fecha_creacion", ascending=False)
            .drop_duplicates(subset="rut", keep="first")
            .reset_index(drop=True)
        )
        
        return df[["rut", "analista_riesgo"]]
        
    except Exception as e:
        print(f"Error al obtener datos de analistas: {e}")
        return pd.DataFrame()

def procesar_datos_manual_evaluation(archivo_path):
    """
    Procesa el archivo manual_evaluation descargado y aplica transformaciones
    """
    try:
        df = pd.read_csv(archivo_path)
        
        # Filtrar por status
        df = df[~df["status"].isin(["FINISHED", "CREATED"])]
        
        # Renombrar columnas
        df = df.rename(columns={
            "idNumber": "rut",
            "resolution": "resolucion_riesgo",
            "manualEvaluationUpdatedDate": "fecha_creacion"
        })
        
        # Seleccionar columnas necesarias
        df = df[["rut", "resolucion_riesgo", "fecha_creacion", "status", "manualEvaluationId"]]
        
        # Procesar resoluciones según status
        df["resolucion_riesgo"] = df["resolucion_riesgo"].astype(str)
        df["status"] = df["status"].astype(str).str.upper()
        
        # Aplicar lógica de transformación
        mask_zero = df["resolucion_riesgo"] == "0"
        mask_ret = df["status"] == "RETURNED_DUE_TO_RISK"
        mask_ref = df["status"] == "REFUSED"
        
        df.loc[mask_zero & mask_ret, "resolucion_riesgo"] = "Devuelto a comercial"
        df.loc[mask_zero & mask_ref, "resolucion_riesgo"] = "Rechazado"
        df.loc[mask_zero & ~mask_ret & ~mask_ref, "resolucion_riesgo"] = "Desconocido"
          # Procesar fechas manteniendo UTC
        df["fecha_creacion"] = pd.to_datetime(df["fecha_creacion"], errors="coerce", utc=True)
        
        return df
        
    except Exception as e:
        print(f"Error al procesar datos manual evaluation: {e}")
        return pd.DataFrame()

def guardar_archivo_actualizado(df, carpeta_id):
    """Guarda el DataFrame procesado en la carpeta de archivos actualizados"""
    try:
        hoy = date.today().strftime("%Y-%m-%d")
        nombre_archivo = f"manual_evaluations_{hoy}.csv"
        ruta_local = os.path.join(RUTA_TEMP, nombre_archivo)
        
        # Crear directorio si no existe
        os.makedirs(RUTA_TEMP, exist_ok=True)
        
        # Guardar archivo localmente
        df.to_csv(ruta_local, index=False)
        
        # Subir a Drive (esto requeriría implementar función de subida en funciones_google)
        # Por ahora solo guardamos localmente
        
        return ruta_local
        
    except Exception as e:
        print(f"Error al guardar archivo actualizado: {e}")
        return None

def agregar_datos_analistas(df_graf, incluir_analistas=False):
    """
    Agrega información de analistas al DataFrame principal
    Solo si incluir_analistas es True (cuando se selecciona filtro único)
    """
    if not incluir_analistas:
        df_graf["analista_riesgo"] = "N/A"
        return df_graf
    
    try:
        df_analistas = obtener_datos_analistas()
        
        if df_analistas.empty:
            df_graf["analista_riesgo"] = "Desconocido"
            return df_graf
        
        # Asegurar tipos de datos
        df_graf["rut"] = df_graf["rut"].astype(str)
        df_analistas["rut"] = df_analistas["rut"].astype(str)
        
        # Hacer merge
        df_graf = df_graf.merge(
            df_analistas,
            on="rut",
            how="left"
        )
        
        # Rellenar valores faltantes
        df_graf["analista_riesgo"] = df_graf["analista_riesgo"].fillna("Desconocido")
        
        return df_graf
        
    except Exception as e:
        print(f"Error al agregar datos de analistas: {e}")
        df_graf["analista_riesgo"] = "Desconocido"
        return df_graf

def obtener_datos_principales(incluir_analistas=False):
    """
    Función principal que gestiona todo el flujo de obtención de datos
    """
    try:
        # Crear directorio temporal si no existe
        os.makedirs(RUTA_TEMP, exist_ok=True)
        
        # Verificar si necesita actualización
        necesita_actualizacion, archivo_existente = verificar_necesidad_actualizacion()
        
        if not necesita_actualizacion and archivo_existente is not None:
            # Usar archivo existente del día
            ruta_archivo = os.path.join(RUTA_TEMP, f"cached_{archivo_existente['Nombre']}")
            
            # Si no existe localmente, descargarlo
            if not os.path.exists(ruta_archivo):
                ruta_archivo = bajar_archivo_por_id(archivo_existente["ID"], RUTA_TEMP)
            
        else:
            # Obtener archivo más reciente y descargarlo
            archivo_reciente = obtener_archivo_mas_reciente()
            
            if archivo_reciente is None:
                raise ValueError("No se pudo obtener archivo más reciente")
            
            ruta_archivo = bajar_archivo_por_id(archivo_reciente["ID"], RUTA_TEMP)
        
        # Procesar datos
        df_graf = procesar_datos_manual_evaluation(ruta_archivo)
        
        if df_graf.empty:
            raise ValueError("No se pudieron procesar los datos")
        
        # Agregar datos de analistas si es necesario
        df_graf = agregar_datos_analistas(df_graf, incluir_analistas)
        
        # Si fue necesaria actualización, guardar archivo
        if necesita_actualizacion:
            guardar_archivo_actualizado(df_graf, ID_CARPETA_ACTUALIZADOS)
        
        return df_graf
        
    except Exception as e:
        print(f"Error en obtener_datos_principales: {e}")
        # Retornar DataFrame vacío en caso de error
        return pd.DataFrame()

# Función de compatibilidad con código existente
def cargar_datos(incluir_analistas=False):
    """Wrapper para compatibilidad con el dashboard existente"""
    return obtener_datos_principales(incluir_analistas)
