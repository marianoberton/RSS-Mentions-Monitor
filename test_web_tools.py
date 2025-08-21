#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que la interfaz web de herramientas funciona correctamente.
Ejecuta este script para probar las nuevas rutas y funcionalidades.
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_tools_page(base_url="http://localhost:5000"):
    """Prueba que la página de herramientas carga correctamente."""
    print("🔍 Probando página de herramientas...")
    
    try:
        response = requests.get(f"{base_url}/tools", timeout=10)
        
        if response.status_code == 200:
            print("✅ Página de herramientas carga correctamente")
            
            # Verificar que contiene elementos esperados
            content = response.text
            expected_elements = [
                "Herramientas y Diagnósticos",
                "Verificar Efectividad",
                "Verificar Estado",
                "run-tool",
                "data-script"
            ]
            
            missing_elements = []
            for element in expected_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️  Elementos faltantes en la página: {missing_elements}")
            else:
                print("✅ Todos los elementos esperados están presentes")
                
            return True
        else:
            print(f"❌ Error al cargar página: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_script_execution(base_url="http://localhost:5000", script="verificar_estado.py"):
    """Prueba la ejecución de un script específico."""
    print(f"🔧 Probando ejecución de {script}...")
    
    try:
        response = requests.post(
            f"{base_url}/tools/run/{script}",
            headers={'Content-Type': 'application/json'},
            timeout=60  # 1 minuto para scripts de prueba
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Script ejecutado - Éxito: {data.get('success', False)}")
            print(f"📊 Código de retorno: {data.get('return_code', 'N/A')}")
            
            if data.get('output'):
                output_preview = data['output'][:200] + "..." if len(data['output']) > 200 else data['output']
                print(f"📝 Salida (preview): {output_preview}")
            
            if data.get('error'):
                error_preview = data['error'][:200] + "..." if len(data['error']) > 200 else data['error']
                print(f"⚠️  Error: {error_preview}")
                
            return data.get('success', False)
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            try:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('error', 'Error desconocido')}")
            except:
                print(f"❌ Respuesta: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_invalid_script(base_url="http://localhost:5000"):
    """Prueba que los scripts no permitidos son rechazados."""
    print("🔒 Probando seguridad - script no permitido...")
    
    try:
        response = requests.post(
            f"{base_url}/tools/run/script_malicioso.py",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            if "no está permitido" in data.get('error', ''):
                print("✅ Seguridad funcionando - script rechazado correctamente")
                return True
            else:
                print(f"⚠️  Respuesta inesperada: {data}")
                return False
        else:
            print(f"❌ Código de estado inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_api_stats(base_url="http://localhost:5000"):
    """Prueba que la API de estadísticas funciona."""
    print("📊 Probando API de estadísticas...")
    
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API de estadísticas funciona")
            print(f"📈 Estadísticas disponibles: {list(data.keys())}")
            return True
        else:
            print(f"❌ Error en API: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal de pruebas."""
    print("🧪 PRUEBAS DE INTERFAZ WEB DE HERRAMIENTAS")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Configuración
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🌐 URL base: {base_url}")
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Página de herramientas", lambda: test_tools_page(base_url)),
        ("API de estadísticas", lambda: test_api_stats(base_url)),
        ("Ejecución de script válido", lambda: test_script_execution(base_url, "verificar_estado.py")),
        ("Seguridad - script inválido", lambda: test_invalid_script(base_url))
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔬 PRUEBA: {test_name}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            duration = end_time - start_time
            results.append((test_name, result, duration))
            
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"⏱️  Duración: {duration:.2f}s")
            print(f"🎯 Resultado: {status}")
            
        except Exception as e:
            print(f"💥 Error inesperado: {e}")
            results.append((test_name, False, 0))
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result, duration in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} | {test_name} ({duration:.2f}s)")
        if result:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! La interfaz web está funcionando correctamente.")
        return 0
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar la configuración.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)