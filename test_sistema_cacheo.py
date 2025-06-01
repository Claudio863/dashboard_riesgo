#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de cacheo diario
"""

import os
import sys
from datetime import datetime, date
import pandas as pd

def test_funciones_google():
    """Prueba las funciones de Google Drive"""
    print("🧪 PRUEBA 1: Importando funciones_google.py")
    try:
        from funciones_google import (
            gestionar_archivo_busqueda_diario,
            verificar_estado_actualizacion_drive,
            obtener_archivo_historico_desde_drive
        )
        print("✅ Importación exitosa de funciones_google.py")
        return True
    except ImportError as e:
        print(f"❌ Error importando funciones_google.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_verificacion_estado():
    """Prueba la verificación de estado sin descargar archivos"""
    print("\n🧪 PRUEBA 2: Verificando estado de archivos en Google Drive")
    try:
        from funciones_google import verificar_estado_actualizacion_drive
        
        # Esta función no requiere credenciales, solo verifica la lógica
        estado = verificar_estado_actualizacion_drive()
        
        print(f"📊 Estado del archivo:")
        print(f"   - Existe: {estado['existe']}")
        print(f"   - Actualizado: {estado['actualizado']}")
        print(f"   - Fecha creación: {estado['fecha_creacion']}")
        print(f"   - Mensaje: {estado['mensaje']}")
        
        return True
    except Exception as e:
        print(f"❌ Error en verificación de estado: {e}")
        return False

def test_archivo_respaldo():
    """Prueba la función de archivo de respaldo"""
    print("\n🧪 PRUEBA 3: Probando función archivo_actualizado() de respaldo")
    try:
        from funciones_google import archivo_actualizado
        
        # Crear un archivo CSV de prueba
        datos_prueba = {
            'fecha_creacion': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'ejecutivo': ['Test User'],
            'rut_cliente': ['12345678-9'],
            'estado': ['Activo'],
            'producto': ['Prueba']
        }
        
        df_prueba = pd.DataFrame(datos_prueba)
        archivo_test = f"datos_{date.today().strftime('%Y-%m-%d')}.csv"
        df_prueba.to_csv(archivo_test, index=False)
        
        print(f"📝 Archivo de prueba creado: {archivo_test}")
        
        # Probar la función de respaldo
        df_resultado = archivo_actualizado()
        
        if not df_resultado.empty:
            print(f"✅ Función archivo_actualizado() funcionando correctamente")
            print(f"📊 Datos cargados: {len(df_resultado)} filas")
            return True, archivo_test
        else:
            print(f"⚠️ Función archivo_actualizado() retornó DataFrame vacío")
            return False, archivo_test
            
    except Exception as e:
        print(f"❌ Error en prueba de archivo de respaldo: {e}")
        return False, None

def test_dashboard_import():
    """Prueba la sintaxis del dashboard sin ejecutarlo"""
    print("\n🧪 PRUEBA 4: Verificando sintaxis del dashboard")
    try:
        import ast
        
        # Leer el archivo dashboard.py
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            codigo_dashboard = f.read()
        
        # Verificar que no tenga errores de sintaxis
        ast.parse(codigo_dashboard)
        print("✅ Dashboard sin errores de sintaxis")
        
        # Verificar que no tenga referencias problemáticas
        if 'lector_reporte_automático' in codigo_dashboard:
            print("❌ Dashboard aún contiene referencias a lector_reporte_automático")
            return False
        
        print("✅ Dashboard no contiene referencias problemáticas")
        return True
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en dashboard: {e}")
        return False
    except Exception as e:
        print(f"❌ Error verificando dashboard: {e}")
        return False

def test_integracion_completa():
    """Prueba la integración completa del sistema"""
    print("\n🧪 PRUEBA 5: Prueba de integración completa")
    try:
        from funciones_google import gestionar_archivo_busqueda_diario
        
        print("🔄 Intentando gestionar archivo de búsqueda diario...")
        print("(Nota: Esta prueba podría fallar sin credenciales de Google Drive)")
        
        # Esto debería usar el sistema de fallback si no hay credenciales
        ruta_archivo = gestionar_archivo_busqueda_diario()
        
        if ruta_archivo and os.path.exists(ruta_archivo):
            print(f"✅ Sistema de gestión funcionando: {ruta_archivo}")
            return True, ruta_archivo
        else:
            print(f"⚠️ Sistema de gestión usó fallback o falló")
            return False, None
            
    except Exception as e:
        print(f"❌ Error en integración completa: {e}")
        return False, None

def cleanup_test_files(*archivos):
    """Limpia archivos de prueba"""
    print("\n🧹 LIMPIEZA: Eliminando archivos de prueba")
    for archivo in archivos:
        if archivo and os.path.exists(archivo):
            try:
                os.remove(archivo)
                print(f"🗑️ Archivo eliminado: {archivo}")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar {archivo}: {e}")

def main():
    """Función principal de pruebas"""
    print("=" * 60)
    print("🔬 SISTEMA DE PRUEBAS - CACHEO DIARIO")
    print("=" * 60)
    print(f"⏰ Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 Directorio actual: {os.getcwd()}")
    print()
    
    archivos_para_limpiar = []
    resultados = []
    
    # Ejecutar pruebas
    resultados.append(test_funciones_google())
    resultados.append(test_verificacion_estado())
    
    resultado_respaldo, archivo_test = test_archivo_respaldo()
    resultados.append(resultado_respaldo)
    if archivo_test:
        archivos_para_limpiar.append(archivo_test)
    
    resultados.append(test_dashboard_import())
    
    resultado_integracion, archivo_integracion = test_integracion_completa()
    resultados.append(resultado_integracion)
    if archivo_integracion:
        archivos_para_limpiar.append(archivo_integracion)
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    pruebas_exitosas = sum(resultados)
    total_pruebas = len(resultados)
    
    print(f"✅ Pruebas exitosas: {pruebas_exitosas}/{total_pruebas}")
    print(f"❌ Pruebas fallidas: {total_pruebas - pruebas_exitosas}/{total_pruebas}")
    
    if pruebas_exitosas == total_pruebas:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print("✅ El sistema de cacheo diario está funcionando correctamente")
    else:
        print(f"\n⚠️ Algunas pruebas fallaron")
        print("🔧 Revisa los errores anteriores para debugging")
    
    # Limpiar archivos de prueba
    cleanup_test_files(*archivos_para_limpiar)
    
    print(f"\n🏁 Pruebas completadas a las {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
