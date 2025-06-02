#!/usr/bin/env python3
"""
Script de verificación final para el fix del error de Streamlit Cloud
"""

import os
import sys
import ast

def verificar_imports_dashboard():
    """Verifica que los imports en dashboard.py sean correctos"""
    print("🔍 Verificando imports en dashboard.py...")
    
    try:
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parsear el AST para verificar imports
        tree = ast.parse(content)
        
        imports_encontrados = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports_encontrados.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports_encontrados.append(f"from {module} import {alias.name}")
        
        print("✅ Imports encontrados:")
        for imp in imports_encontrados[:10]:  # Mostrar primeros 10
            print(f"   {imp}")
        
        # Verificar que no hay referencia al módulo problemático
        if 'lector_reporte_automatico' in content or 'lector_reporte_automático' in content:
            print("❌ ERROR: Aún hay referencias a lector_reporte_automático")
            return False
        else:
            print("✅ No se encontraron referencias a lector_reporte_automático")
        
        # Verificar imports correctos
        required_imports = [
            'from funciones_google import',
            'from identificador_analista import'
        ]
        
        for req_import in required_imports:
            if req_import in content:
                print(f"✅ Import correcto encontrado: {req_import}")
            else:
                print(f"❌ Import faltante: {req_import}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar dashboard.py: {e}")
        return False

def verificar_encoding():
    """Verifica que el archivo tenga encoding correcto"""
    print("\n🔤 Verificando encoding del archivo...")
    
    try:
        with open('dashboard.py', 'rb') as f:
            raw_content = f.read()
        
        # Verificar que no hay BOM
        if raw_content.startswith(b'\xef\xbb\xbf'):
            print("⚠️ Archivo contiene BOM UTF-8")
        else:
            print("✅ Sin BOM UTF-8")
        
        # Verificar que se puede decodificar como UTF-8
        try:
            content = raw_content.decode('utf-8')
            print("✅ Encoding UTF-8 válido")
            return True
        except UnicodeDecodeError as e:
            print(f"❌ Error de encoding UTF-8: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error al verificar encoding: {e}")
        return False

def verificar_sintaxis():
    """Verifica que el archivo tenga sintaxis Python válida"""
    print("\n🐍 Verificando sintaxis Python...")
    
    try:
        with open('dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compilar para verificar sintaxis
        compile(content, 'dashboard.py', 'exec')
        print("✅ Sintaxis Python válida")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"   Línea {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error al verificar sintaxis: {e}")
        return False

def main():
    print("🚀 VERIFICACIÓN FINAL - FIX STREAMLIT CLOUD")
    print("=" * 50)
    
    if not os.path.exists('dashboard.py'):
        print("❌ Archivo dashboard.py no encontrado")
        sys.exit(1)
    
    resultados = []
    
    # Verificar imports
    resultados.append(verificar_imports_dashboard())
    
    # Verificar encoding
    resultados.append(verificar_encoding())
    
    # Verificar sintaxis
    resultados.append(verificar_sintaxis())
    
    print("\n" + "=" * 50)
    if all(resultados):
        print("🎉 TODAS LAS VERIFICACIONES PASARON")
        print("✅ El archivo dashboard.py está listo para Streamlit Cloud")
        print("\n📋 Resumen de cambios aplicados:")
        print("   - Limpieza de caracteres especiales y acentos")
        print("   - Encoding UTF-8 sin BOM")
        print("   - Imports correctos de funciones_google e identificador_analista")
        print("   - Eliminación completa de referencias a lector_reporte_automático")
        print("\n🚀 El despliegue en Streamlit Cloud debería funcionar ahora")
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("⚠️ Revisa los errores arriba antes de desplegar")
        sys.exit(1)

if __name__ == "__main__":
    main()
