#!/usr/bin/env python3
"""
Test de verificación de importaciones para corregir errores de Streamlit Cloud
"""

def test_imports():
    """Prueba todas las importaciones del dashboard"""
    print("🧪 Iniciando test de importaciones...")
    
    try:
        # Test 1: Importar funciones_google
        print("📦 Testeando funciones_google.py...")
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from funciones_google import login, listar_archivos_carpeta
        print("✅ funciones_google.py importado correctamente")
        
        # Test 2: Verificar función archivo_actualizado
        from funciones_google import archivo_actualizado
        print("✅ Función archivo_actualizado encontrada")
        
        # Test 3: Importar identificador_analista
        from identificador_analista import dataframe_cola_aws
        print("✅ identificador_analista.py importado correctamente")
        
        # Test 4: Verificar estructura de dashboard.py
        print("📦 Verificando estructura de dashboard.py...")
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'lector_reporte_automático' in content:
                print("❌ ERROR: dashboard.py aún contiene referencias a lector_reporte_automático")
                return False
            else:
                print("✅ dashboard.py no contiene referencias problemáticas")
        
        print("✅ Todos los tests de importación pasaron exitosamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n🎉 LISTO PARA STREAMLIT CLOUD")
        print("El dashboard debería funcionar correctamente en Streamlit Cloud")
    else:
        print("\n⚠️ REQUIERE CORRECCIONES")
        print("Hay problemas que deben resolverse antes del despliegue")
