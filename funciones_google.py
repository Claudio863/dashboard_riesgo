



from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import pandas as pd
import pandas as pd
from collections import defaultdict
import time
import pandas as pd
import os
from PyPDF2 import PdfReader, PdfWriter
from io import StringIO
from openai import OpenAI



def login():
    CREDENTIALS_FILE = 'drive_automat.json'
    # Configuración para que PyDrive2 use el archivo de credenciales correcto
    GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = CREDENTIALS_FILE
    gauth = GoogleAuth()
    
    # Modificar el flujo de autenticación para obtener el refresh_token
    gauth.settings['client_config_backend'] = 'file'
    gauth.settings['oauth_scope'] = ['https://www.googleapis.com/auth/drive']
    gauth.settings['get_refresh_token'] = True
    
    # Forzar `access_type` a 'offline' y `approval_prompt` a 'force' para garantizar el refresh_token
    gauth.settings['access_type'] = 'offline'
    gauth.settings['approval_prompt'] = 'force'

    # Intentar cargar las credenciales guardadas
    gauth.LoadCredentialsFile("credentials.json")
    if gauth.credentials is None:
        # Si no existen, lanzar el flujo de autenticación web para obtener credenciales nuevas
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refrescar el token si ha expirado
        gauth.Refresh()
    else:
        # Autorizar con las credenciales existentes
        gauth.Authorize()

    # Guardar las credenciales en un archivo para reutilizarlas en el futuro
    gauth.SaveCredentialsFile("credentials.json")
    
    # Retornar el objeto GoogleDrive para realizar operaciones con la API
    drive = GoogleDrive(gauth)
    return drive

def listar_archivos_carpeta(folder_id):
    credenciales = login()
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


def bajar_archivo_por_id(id_drive, ruta_descarga):
    try:
        credenciales = login()
        archivo = credenciales.CreateFile({'id': id_drive})
        nombre_archivo = archivo['title']
        ruta_completa = ruta_descarga + nombre_archivo
        archivo.GetContentFile(ruta_completa)
        return ruta_completa
    except Exception as e:
        print(f"Error al bajar el archivo con ID {id_drive}: {e}")
        return None
