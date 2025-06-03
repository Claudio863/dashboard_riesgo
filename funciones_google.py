from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import pandas as pd
from collections import defaultdict
import time
import os
from PyPDF2 import PdfReader, PdfWriter
from io import StringIO
from openai import OpenAI
import re
from typing import Optional
import json
import tempfile

# Función de respaldo para cargar datos
def archivo_actualizado():
    """
    Función de respaldo para cargar datos desde archivo CSV local
    Proporciona datos de fallback cuando no hay acceso a Google Drive
    """
    try:
        import glob
        archivos_csv = glob.glob("datos_*.csv")
        if archivos_csv:
            archivo_mas_reciente = max(archivos_csv)
            df = pd.read_csv(archivo_mas_reciente)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error cargando archivo local: {e}")
        return pd.DataFrame()


def login():
    """
    Función de login que funciona tanto localmente como en Streamlit Cloud
    - Local: usa archivos JSON de credenciales
    - Streamlit Cloud: usa st.secrets
    """
    try:
        import streamlit as st
        
        # Verificar si estamos en Streamlit Cloud (secrets disponibles)
        if hasattr(st, 'secrets') and 'google_drive' in st.secrets:
            print("🔑 Autenticando con Streamlit Cloud secrets...")
            
            # Crear diccionario de credenciales desde secrets
            credentials_dict = {
                "type": "service_account",
                "project_id": st.secrets["google_drive"]["project_id"],
                "private_key_id": st.secrets["google_drive"]["private_key_id"],
                "private_key": st.secrets["google_drive"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["google_drive"]["client_email"],
                "client_id": st.secrets["google_drive"]["client_id"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": st.secrets["google_drive"]["client_x509_cert_url"]
            }
            
            # Crear archivo temporal para credenciales
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                json.dump(credentials_dict, f)
                temp_creds_path = f.name
            
            try:
                # Configurar PyDrive2 para usar service account
                gauth = GoogleAuth()
                gauth.settings = {
                    'client_config_backend': 'service',
                    'service_config': {
                        'client_json_file_path': temp_creds_path,
                    }
                }
                gauth.ServiceAuth()
                
                print("✅ Autenticación exitosa con service account")
                return GoogleDrive(gauth)
                
            finally:
                # Siempre limpiar archivo temporal
                try:
                    os.unlink(temp_creds_path)
                except:
                    pass
            
        else:
            print("🔑 Autenticando localmente con archivos JSON...")
            
            # Configuración local usando archivos JSON
            CREDENTIALS_FILE = 'drive_automat.json'
            
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"❌ No se encontró {CREDENTIALS_FILE}")
                return None
                
            GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = CREDENTIALS_FILE
            gauth = GoogleAuth()
            
            # Configuración para OAuth local
            gauth.settings['client_config_backend'] = 'file'
            gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
            gauth.settings['get_refresh_token'] = True
            gauth.settings['access_type'] = 'offline'
            gauth.settings['approval_prompt'] = 'force'
            
            # Intentar cargar credenciales guardadas
            gauth.LoadCredentialsFile("mycreds.txt")
            
            if gauth.credentials is None:
                print("🔄 Realizando autenticación web...")
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                print("🔄 Refrescando token expirado...")
                gauth.Refresh()
            else:
                print("✅ Usando credenciales existentes")
                gauth.Authorize()
            
            # Guardar credenciales para la próxima vez
            gauth.SaveCredentialsFile("mycreds.txt")
            
            return GoogleDrive(gauth)
            
    except Exception as e:
        print(f"❌ Error en login: {e}")
        return None

def listar_archivos_carpeta(folder_id):
    """
    Lista todos los archivos en una carpeta de Google Drive
    """
    credenciales = login()
    if credenciales is None:
        print("❌ No se pudo conectar a Google Drive")
        return pd.DataFrame()
        
    query = f"'{folder_id}' in parents and trashed = false"
    nombres = []
    id_archive = []
    type_archive = []
    fechas_creacion = []
    
    try:
        lista_archivos = credenciales.ListFile({'q': query}).GetList()
        if not lista_archivos:
            print(f"No se encontraron archivos en la carpeta con ID {folder_id}.")
        else:
            for f in lista_archivos:
                nombres.append(f['title'])
                id_archive.append(f['id'])
                type_archive.append(f['mimeType'])
                fechas_creacion.append(f['createdDate'])

    except Exception as e:
        print(f"Se produjo un error al listar los archivos: {e}")
        
    df_carpeta = pd.DataFrame({
        'Nombre': nombres,
        'ID': id_archive,
        'Tipo': type_archive,
        'Fecha Creación': fechas_creacion
    })
    return df_carpeta
# ───────────────────────────────────────────────
# 1) Utilidad para nombres seguros
# ───────────────────────────────────────────────
_INVALID_CHARS = r'[<>:"/\\|?*]'

def safe_filename(name: str, replacement: str = "-") -> str:
    """
    Devuelve `name` sin caracteres ilegales para rutas de Windows.
    """
    return re.sub(_INVALID_CHARS, replacement, name)

def bajar_archivo_por_id(id_drive: str, ruta_descarga: str) -> Optional[str]:
    """
    Descarga un archivo desde Drive (PyDrive2) y lo guarda en `ruta_descarga`,
    devolviendo la ruta completa ya saneada. Si algo falla, retorna None.
    """
    try:
        credenciales = login()
        if credenciales is None:
            print("❌ No se pudo conectar a Google Drive para descargar archivo")
            return None
            
        archivo = credenciales.CreateFile({'id': id_drive})
        
        # Nombre original y nombre seguro
        nombre_original = archivo['title']
        nombre_seguro   = safe_filename(nombre_original)

        # Construye la ruta destino
        ruta_completa = os.path.join(ruta_descarga, nombre_seguro)
        os.makedirs(ruta_descarga, exist_ok=True)      # crea la carpeta si falta

        archivo.GetContentFile(ruta_completa)
        print(f"✅ Archivo descargado: {nombre_seguro}")
        return ruta_completa

    except Exception as e:
        print(f"❌ Error al bajar el archivo con ID {id_drive}: {e}")
        return None

def subir_archivo(ruta_archivo_local: str, nombre_archivo: str = None, descripcion: str = "Archivo subido automáticamente") -> Optional[str]:
    """
    Sube un archivo local a Google Drive usando PyDrive2.
    
    Args:
        ruta_archivo_local (str): Ruta local del archivo a subir
        nombre_archivo (str, optional): Nombre del archivo en Drive. Si es None, usa el nombre original
        descripcion (str): Descripción del archivo en Drive
    
    Returns:
        Optional[str]: ID del archivo subido o None si hay error
    """
    import random
    from datetime import datetime
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(ruta_archivo_local):
            print(f"Error: El archivo {ruta_archivo_local} no existe.")
            return None
        
        # Obtener credenciales de Drive
        credenciales = login()
        
        # Generar ID único si no se especifica nombre
        if nombre_archivo is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            id_unico = random.randint(10000, 99999)
            nombre_original = os.path.basename(ruta_archivo_local)
            nombre_sin_extension, extension = os.path.splitext(nombre_original)
            nombre_archivo = f"{timestamp}_{id_unico}_{nombre_sin_extension}{extension}"
        
        # Limpiar nombre de archivo para evitar caracteres problemáticos
        nombre_archivo = safe_filename(nombre_archivo)
        
        # ID de la carpeta de destino
        folder_id = "1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"
        
        # Crear el archivo en Drive
        archivo_drive = credenciales.CreateFile({
            'title': nombre_archivo,
            'description': descripcion,
            'parents': [{'id': folder_id}]
        })
        
        # Subir el contenido del archivo
        archivo_drive.SetContentFile(ruta_archivo_local)
        archivo_drive.Upload()
        
        print(f"✅ Archivo subido exitosamente: {nombre_archivo}")
        print(f"📁 ID del archivo: {archivo_drive['id']}")
        
        return archivo_drive['id']
        
    except Exception as e:
        print(f"❌ Error al subir el archivo: {e}")
        return None

def registrar_error(ejecutivo: str, error: str, ruta_carpeta_local: str = "registros_errores") -> Optional[str]:
    """
    Registra un error en un archivo de texto y lo sube a Google Drive.
    
    Args:
        ejecutivo (str): Nombre del ejecutivo o usuario que generó el error
        error (str): Descripción del error
        ruta_carpeta_local (str): Carpeta local donde guardar temporalmente el archivo
    
    Returns:
        Optional[str]: ID del archivo subido o None si hay error
    """
    import random
    from datetime import datetime
    
    try:
        # Generar ID único para el error
        id_error = random.randint(10000, 99999)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear carpeta local si no existe
        os.makedirs(ruta_carpeta_local, exist_ok=True)
        
        # Verificar si la carpeta fue creada
        if os.path.exists(ruta_carpeta_local):
            print(f"📁 Carpeta creada/verificada en: {ruta_carpeta_local}")
        else:
            print("❌ Error al crear la carpeta de registros.")
            return None
        
        # Crear el archivo de error con información detallada
        nombre_archivo_error = f"error_{timestamp}_{id_error}_{ejecutivo}.txt"
        ruta_archivo_error = os.path.join(ruta_carpeta_local, nombre_archivo_error)
        
        contenido_error = f"""REGISTRO DE ERROR
==================
Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Ejecutivo/Usuario: {ejecutivo}
ID del Error: {id_error}

DESCRIPCIÓN DEL ERROR:
{error}

INFORMACIÓN ADICIONAL:
- Sistema: Dashboard de Riesgo
- Archivo generado automáticamente
"""
          # Escribir el error al archivo
        with open(ruta_archivo_error, "w", encoding="utf-8") as file:
            file.write(contenido_error)
        
        print(f"📝 Archivo de error creado: {ruta_archivo_error}")
        
        # Subir el archivo a Google Drive
        id_archivo_drive = subir_archivo(
            ruta_archivo_error, 
            nombre_archivo_error,
            f"Registro de error - {ejecutivo} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if id_archivo_drive:
            print(f"✅ Error registrado exitosamente. ID del archivo: {id_archivo_drive}")
            
            # Limpiar archivo local después de subir exitosamente
            try:
                os.remove(ruta_archivo_error)
                print(f"🗑️ Archivo local temporal eliminado: {ruta_archivo_error}")
            except Exception as cleanup_error:
                print(f"⚠️ No se pudo eliminar el archivo temporal: {cleanup_error}")
        else:
            print("❌ Error al subir el archivo de registro a Google Drive.")
        
        return id_archivo_drive
        
    except Exception as e:
        print(f"❌ Error al registrar el error: {e}")
        return None


def gestionar_archivo_busqueda_diario(folder_id="1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"):
    """
    Gestiona el archivo de búsqueda diario en Google Drive con detección automática de actualización.
    
    1. Verifica si existe un archivo del día actual actualizado después de las 10:00 AM
    2. Si existe y está actualizado, lo descarga y retorna la ruta local
    3. Si no existe o está desactualizado, genera uno nuevo y lo sube
    4. Retorna la ruta del archivo local para ser usado
    
    Args:
        folder_id (str): ID del folder de Google Drive donde almacenar los archivos
          Returns:
        str: Ruta del archivo local descargado/generado
    """
    from datetime import date, datetime, time
    
    try:
        # Obtener fecha y hora actual
        ahora = datetime.now()
        hoy = date.today().strftime("%Y-%m-%d")
        hora_limite = time(10, 0)  # 10:00 AM
        
        nombre_archivo_esperado = f"busqueda_diaria_{hoy}.csv"
        
        print(f"🔍 Buscando archivo del día {hoy} en Google Drive...")
        print(f"⏰ Hora actual: {ahora.strftime('%H:%M:%S')}")
        
        # Listar archivos en el folder
        df_archivos = listar_archivos_carpeta(folder_id)
        
        archivo_hoy_id = None
        archivo_hoy_encontrado = False
        archivo_actualizado_hoy = False
        
        if df_archivos.empty:
            print("📂 No se encontraron archivos en el folder")
        else:
            # Buscar archivo del día actual
            archivo_hoy = df_archivos[df_archivos["Nombre"] == nombre_archivo_esperado]
            
            if archivo_hoy.empty:
                print(f"📄 No se encontró archivo del día: {nombre_archivo_esperado}")
            else:
                archivo_hoy_encontrado = True
                archivo_info = archivo_hoy.iloc[0]
                archivo_hoy_id = archivo_info["ID"]
                fecha_creacion_str = archivo_info["Fecha Creación"]
                  # Parsear fecha de creación del archivo en Google Drive
                try:
                    # Formato típico: 2024-05-31T14:30:00.000Z
                    fecha_creacion = datetime.fromisoformat(fecha_creacion_str.replace('Z', '+00:00'))
                    fecha_creacion_local = fecha_creacion.replace(tzinfo=None)  # Remover timezone para comparar
                    
                    # Verificar si el archivo fue creado/actualizado después de las 10:00 AM de hoy
                    limite_actualizacion = datetime.combine(date.today(), hora_limite)
                    if fecha_creacion_local >= limite_actualizacion:
                        archivo_actualizado_hoy = True
                        print(f"✅ Archivo encontrado y actualizado: {nombre_archivo_esperado}")
                        print(f"📅 Creado/actualizado: {fecha_creacion_local.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        archivo_actualizado_hoy = False
                        print(f"⚠️ Archivo encontrado pero desactualizado: {nombre_archivo_esperado}")
                        print(f"📅 Creado: {fecha_creacion_local.strftime('%Y-%m-%d %H:%M:%S')} (antes de 10:00 AM)")
                
                except Exception as e:
                    print(f"⚠️ Error parseando fecha de creación: {e}")
                    archivo_actualizado_hoy = False
        
        # Ruta local donde guardar/cargar el archivo
        ruta_local = f"datos_busqueda_{hoy}.csv"
        
        if archivo_hoy_encontrado and archivo_actualizado_hoy:
            # Descargar el archivo actualizado existente
            print(f"📥 Descargando archivo actualizado existente...")
            drive = login()
            archivo = drive.CreateFile({'id': archivo_hoy_id})
            archivo.GetContentFile(ruta_local)
            print(f"✅ Archivo actualizado descargado exitosamente: {ruta_local}")
            
        else:
            # Generar nuevo archivo usando el proceso actual
            if archivo_hoy_encontrado and not archivo_actualizado_hoy:
                print(f"🔄 Archivo existe pero está desactualizado. Sobrescribiendo archivo existente...")
                
                # Obtener datos actualizados usando la función existente
                print(f"🔍 Ejecutando búsqueda completa de datos actualizados...")
                df_actualizado = archivo_actualizado()
                
                # Guardar localmente
                df_actualizado.to_csv(ruta_local, index=False)
                print(f"💾 Archivo generado localmente: {ruta_local}")
                
                # Sobrescribir el archivo existente en Google Drive en lugar de crear uno nuevo
                try:
                    drive = login()
                    archivo_existente = drive.CreateFile({'id': archivo_hoy_id})
                    archivo_existente.SetContentFile(ruta_local)
                    archivo_existente.Upload()
                    print(f"✅ Archivo existente sobrescrito exitosamente en Google Drive (ID: {archivo_hoy_id})")
                    print(f"⏰ Archivo actualizado a las {datetime.now().strftime('%H:%M:%S')}")
                except Exception as e:
                    print(f"⚠️ Error sobrescribiendo archivo existente: {e}")
                    print(f"🔄 Intentando eliminar y crear nuevo archivo...")
                    # Fallback: eliminar y crear nuevo
                    try:
                        archivo_viejo = drive.CreateFile({'id': archivo_hoy_id})
                        archivo_viejo.Trash()
                        print(f"🗑️ Archivo viejo movido a la papelera")
                        
                        # Crear nuevo archivo
                        archivo_drive = drive.CreateFile({
                            'title': nombre_archivo_esperado,
                            'parents': [{'id': folder_id}]
                        })
                        archivo_drive.SetContentFile(ruta_local)
                        archivo_drive.Upload()
                        print(f"✅ Nuevo archivo creado exitosamente (ID: {archivo_drive['id']})")
                    except Exception as fallback_error:
                        print(f"❌ Error en fallback: {fallback_error}")
                        
            else:
                print(f"📊 No se encontró archivo del día. Generando nuevo archivo...")
                
                # Obtener datos actualizados usando la función existente
                print(f"🔍 Ejecutando búsqueda completa de datos actualizados...")
                df_actualizado = archivo_actualizado()
                
                # Guardar localmente                df_actualizado.to_csv(ruta_local, index=False)
                print(f"💾 Archivo generado localmente: {ruta_local}")
                
                # Subir el nuevo archivo a Google Drive
                print(f"📤 Subiendo archivo nuevo a Google Drive...")
                drive = login()
                archivo_drive = drive.CreateFile({
                    'title': nombre_archivo_esperado,
                    'parents': [{'id': folder_id}]
                })
                archivo_drive.SetContentFile(ruta_local)
                archivo_drive.Upload()
                
                print(f"✅ Archivo subido exitosamente a Google Drive con ID: {archivo_drive['id']}")
                print(f"⏰ Archivo creado a las {datetime.now().strftime('%H:%M:%S')}")
        
        return ruta_local
        
    except Exception as e:
        print(f"❌ Error en gestión del archivo de búsqueda diario: {e}")
        # Fallback: usar el proceso local tradicional
        print(f"🔄 Usando proceso local como respaldo...")
        try:
            df_respaldo = archivo_actualizado()
            ruta_respaldo = f"datos_respaldo_{date.today().strftime('%Y-%m-%d')}.csv"
            df_respaldo.to_csv(ruta_respaldo, index=False)
            return ruta_respaldo
        except Exception as fallback_error:
            print(f"❌ Error en proceso de respaldo: {fallback_error}")
            return None


def obtener_archivo_historico_desde_drive(folder_id="1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"):
    """
    Obtiene el archivo histórico más reciente desde Google Drive.
    
    Args:
        folder_id (str): ID del folder de Google Drive
        
    Returns:
        pd.DataFrame: DataFrame con los datos históricos
    """
    try:
        ruta_archivo = gestionar_archivo_busqueda_diario(folder_id)
        
        if ruta_archivo and os.path.exists(ruta_archivo):
            df = pd.read_csv(ruta_archivo)
            print(f"✅ Datos históricos cargados desde: {ruta_archivo}")
            return df
        else:
            print(f"❌ No se pudo obtener el archivo histórico")
            return pd.DataFrame()  # DataFrame vacío como fallback
            
    except Exception as e:
        print(f"❌ Error al obtener archivo histórico: {e}")
        return pd.DataFrame()  # DataFrame vacío como fallback

def verificar_estado_actualizacion_drive(folder_id="1H--_ASpw__9OTnUG1bDfGZ22zRlUpMdF"):
    """
    Verifica el estado de actualización del archivo diario en Google Drive sin descargarlo.
    
    Args:
        folder_id (str): ID del folder de Google Drive
        
    Returns:
        dict: Información sobre el estado del archivo {
            'existe': bool,
            'actualizado': bool,
            'fecha_creacion': datetime,
            'mensaje': str
        }
    """
    from datetime import date, datetime, time
    
    try:
        # Obtener fecha y hora actual
        ahora = datetime.now()
        hoy = date.today().strftime("%Y-%m-%d")
        hora_limite = time(10, 0)  # 10:00 AM
        
        nombre_archivo_esperado = f"busqueda_diaria_{hoy}.csv"
        
        # Listar archivos en el folder
        df_archivos = listar_archivos_carpeta(folder_id)
        
        resultado = {
            'existe': False,
            'actualizado': False,
            'fecha_creacion': None,
            'mensaje': ''
        }
        
        if df_archivos.empty:
            resultado['mensaje'] = "No se encontraron archivos en Google Drive"
            return resultado
        
        # Buscar archivo del día actual
        archivo_hoy = df_archivos[df_archivos["Nombre"] == nombre_archivo_esperado]
        
        if archivo_hoy.empty:
            resultado['mensaje'] = f"No existe archivo para el día {hoy}"
            return resultado
        
        resultado['existe'] = True
        archivo_info = archivo_hoy.iloc[0]
        fecha_creacion_str = archivo_info["Fecha Creación"]
        
        try:
            # Parsear fecha de creación
            fecha_creacion = datetime.fromisoformat(fecha_creacion_str.replace('Z', '+00:00'))
            fecha_creacion_local = fecha_creacion.replace(tzinfo=None)
            resultado['fecha_creacion'] = fecha_creacion_local
            
            # Verificar si está actualizado
            limite_actualizacion = datetime.combine(date.today(), hora_limite)
            
            if fecha_creacion_local >= limite_actualizacion:
                resultado['actualizado'] = True
                resultado['mensaje'] = f"Archivo actualizado (creado a las {fecha_creacion_local.strftime('%H:%M:%S')})"
            else:
                resultado['mensaje'] = f"Archivo desactualizado (creado a las {fecha_creacion_local.strftime('%H:%M:%S')}, antes de 10:00 AM)"
                
        except Exception as e:
            resultado['mensaje'] = f"Error parseando fecha: {e}"
        
        return resultado
        
    except Exception as e:
        return {
            'existe': False,
            'actualizado': False,
            'fecha_creacion': None,
            'mensaje': f"Error verificando estado: {e}"
        }