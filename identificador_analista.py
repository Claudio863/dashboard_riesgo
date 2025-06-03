from funciones_google import *


def dataframe_cola_aws():
    def cargar_google_sheet_en_dataframe(sheet_id, ruta_descarga):
        drive = login()
        if drive is None:
            print(f"❌ No se pudo conectar a Google Drive para sheet {sheet_id}")
            return pd.DataFrame()
            
        try:
            archivo = drive.CreateFile({'id': sheet_id})
            
            # Definir la ruta donde se guardará el CSV temporalmente
            ruta_archivo = os.path.join(ruta_descarga, 'sheet.csv')
            
            # Exportar el Google Sheet como CSV
            archivo.GetContentFile(ruta_archivo, mimetype='text/csv')
            # Leer el CSV en un DataFrame
            df = pd.read_csv(ruta_archivo)
            
            # Limpiar archivo temporal
            try:
                os.remove(ruta_archivo)
            except:
                pass
                
            return df
        except Exception as e:
            print(f"❌ Error descargando Google Sheet {sheet_id}: {e}")
            return pd.DataFrame()

    # ID del Google Sheet (extraído de la URL)
    sheet_id = '1rmSOvyghKM5WpDESHOEnRvVAgtMhELnjys6V9cZ9MG0'
    ruta_descarga = "."  # Usar directorio actual
    sheet_id2='10_ngye6Gevc44m-D2RI2pnpcrVarjXoMrFoYowrTWj4'    # Cargar el Google Sheet en un DataFrame
    try:
        df1 = cargar_google_sheet_en_dataframe(sheet_id, ruta_descarga)
        df2 = cargar_google_sheet_en_dataframe(sheet_id2, ruta_descarga)
        
        # Verificar si se cargaron datos
        if df1.empty and df2.empty:
            print("❌ No se pudieron cargar datos de ninguno de los Google Sheets")
            return pd.DataFrame()
        
        df = pd.concat([df1, df2], ignore_index=True)
        
        if df.empty:
            print("❌ No hay datos para procesar")
            return pd.DataFrame()
            
        df["rut"] = df["full_name"].str.partition("_")[0]
        df = df.drop_duplicates(subset="full_name").copy()
        df.reset_index(drop=True, inplace=True)
        df["fecha_creacion"] = pd.to_datetime(
            df["fecha_creacion"],   # ej. 2024-11-15T17:24:02.685Z
            utc=True,                    # 'Z' → UTC
            errors="coerce"              # NaT si hubiera strings mal formadas
        )
        df = (
            df
                .sort_values("fecha_creacion", ascending=False)   # más nuevas arriba
                .drop_duplicates(subset="rut", keep="first")      # una fila por rut
                .reset_index(drop=True)
        )

        print(f"✅ Datos de analistas cargados exitosamente: {len(df)} registros")
        return df
        
    except Exception as e:
        print(f"❌ Error procesando datos de analistas: {e}")
        return pd.DataFrame()