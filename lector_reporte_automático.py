from funciones_google import login, listar_archivos_carpeta, bajar_archivo_por_id
import pandas as pd
from datetime import date
def archivo_actualizado ():


    anio_actual = str(date.today().year)

    ### Agregar 0 si el mes es menor a 10
    if date.today().month < 10:
        mes_actual = '0' + str(date.today().month)
    print(anio_actual)  
    print(mes_actual)
    
    id_carpeta_raiz="1KRTHc_bOSF4WxX_RIXVpa2_kaypxMMYP"


    carp_raiz=listar_archivos_carpeta(id_carpeta_raiz)
    anio=carp_raiz[carp_raiz["Nombre"]==anio_actual]
    carp_anio=listar_archivos_carpeta(anio["ID"].values[0])
    mes=carp_anio[carp_anio["Nombre"]==mes_actual]
    carp_mes=listar_archivos_carpeta(mes["ID"].values[0])


    # Supongamos que ya tienes el DataFrame
    # carp_mes["Fecha Creación"]  →  dtype object (str)

    # 1) Parsear a datetime con zona UTC
    carp_mes["Fecha Creación"] = pd.to_datetime(
        carp_mes["Fecha Creación"],        # serie de strings
        utc=True,                          # reconoce la Z como UTC
        errors="coerce"                    # NaT si alguna cadena está mal formada
    )

    # Resultado: dtype = datetime64[ns, UTC]

    # Asegúrate de que la columna ya es datetime ----------
# (Si seguiste los pasos anteriores debería serlo;
#  si no, repite la conversión a datetime con utc=True)
    carp_mes["Fecha Creación"] = pd.to_datetime(
        carp_mes["Fecha Creación"], utc=True, errors="coerce"
    )

    # -----------------------------------------------------
    # Ordenar por la fecha más actual (descendente)
    carp_mes = (
        carp_mes
            .sort_values("Fecha Creación", ascending=False)  # ↓↓ más nuevas arriba
            .reset_index(drop=True)                          # opcional: reindexa 0…n-1
    )
    carp_mes= carp_mes[carp_mes["Tipo"]=="text/csv"]

    reporte_actualizado_ev_manual=carp_mes.iloc[0]
    ruta="temp_archives/"
    archivo=bajar_archivo_por_id(reporte_actualizado_ev_manual["ID"],ruta)
    reporte_manuals_evaluations_uptd=pd.read_csv(archivo)
    reporte_manuals_evaluations_uptd
    # Filtra las filas cuyo 'status' NO esté en la lista
    reporte_manuals_evaluations_uptd = (
        reporte_manuals_evaluations_uptd
            [~reporte_manuals_evaluations_uptd["status"].isin(["FINISHED", "CREATED"])]
    )
    df_graf=reporte_manuals_evaluations_uptd.rename(columns={"idNumber": "rut",
                                                         "resolution":"resolucion_riesgo",
                                                            "manualEvaluationUpdatedDate":"fecha_creacion"})
    df_graf=df_graf[["rut","resolucion_riesgo","fecha_creacion","status"]]
    

    import pandas as pd
    import numpy as np

    # 1) Asegúrate de que ambas columnas son texto
    df_graf["resolucion_riesgo"] = df_graf["resolucion_riesgo"].astype(str)
    df_graf["status"]            = df_graf["status"].astype(str).str.upper()   # mayúsculas p/consistencia

    # 2) Máscaras
    mask_zero = df_graf["resolucion_riesgo"] == "0"
    mask_ret  = df_graf["status"] == "RETURNED_DUE_TO_RISK"
    mask_ref  = df_graf["status"] == "REFUSED"

    # 3) Asignaciones
    df_graf.loc[mask_zero &  mask_ret,               "resolucion_riesgo"] = "Devuelto a comercial"
    df_graf.loc[mask_zero &  mask_ref,               "resolucion_riesgo"] = "Rechazado"
    df_graf.loc[mask_zero & ~mask_ret & ~mask_ref,   "resolucion_riesgo"] = "Desconocido"

    return df_graf






