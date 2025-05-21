from funciones_drive import *
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
    archivo=bajar_archivo_por_id(reporte_actualizado_ev_manual["ID"])


