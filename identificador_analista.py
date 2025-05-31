from funciones_google import *


def dataframe_cola_aws():
    def cargar_google_sheet_en_dataframe(sheet_id, ruta_descarga):
        drive = login()
        archivo = drive.CreateFile({'id': sheet_id})
        
        # Definir la ruta donde se guardará el CSV temporalmente
        ruta_archivo = os.path.join(ruta_descarga, 'sheet.csv')
        
        # Exportar el Google Sheet como CSV
        archivo.GetContentFile(ruta_archivo, mimetype='text/csv')
        
        # Leer el CSV en un DataFrame
        df = pd.read_csv(ruta_archivo)
        return df

    # ID del Google Sheet (extraído de la URL)
    sheet_id = '1rmSOvyghKM5WpDESHOEnRvVAgtMhELnjys6V9cZ9MG0'
    ruta_descarga = r'C:\Users\claud\OneDrive\Escritorio\Info\Proyectos\AWS_Riesk\Masive_extraction_json'
    sheet_id2='10_ngye6Gevc44m-D2RI2pnpcrVarjXoMrFoYowrTWj4'

    # Cargar el Google Sheet en un DataFrame
    df1 = cargar_google_sheet_en_dataframe(sheet_id, ruta_descarga)
    df2 = cargar_google_sheet_en_dataframe(sheet_id2, ruta_descarga)
    df=pd.concat([df1,df2])
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

    return df