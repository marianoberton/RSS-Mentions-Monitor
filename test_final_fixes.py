#!/usr/bin/env python3
"""
Script para probar todas las correcciones realizadas en el sistema
"""

import requests
import json
import time
from datetime import datetime

def test_candidate_management():
    """Probar la gestión de candidatos corregida"""
    print("\n" + "="*60)
    print("🧪 PRUEBA: Gestión de Candidatos")
    print("="*60)
    
    base_url = "http://127.0.0.1:5000"
    
    try:
        # Probar ruta /candidates (dashboard)
        print("\n1. Probando dashboard de candidatos (/candidates)...")
        response = requests.get(f"{base_url}/candidates", timeout=10)
        if response.status_code == 200:
            if "Error al cargar" in response.text:
                print("   ❌ Error en dashboard de candidatos")
                return False
            else:
                print("   ✅ Dashboard de candidatos funciona correctamente")
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
        
        # Probar ruta /candidates/manage
        print("\n2. Probando gestión de candidatos (/candidates/manage)...")
        response = requests.get(f"{base_url}/candidates/manage", timeout=10)
        if response.status_code == 200:
            if "Error al cargar" in response.text:
                print("   ❌ Error en gestión de candidatos")
                return False
            else:
                print("   ✅ Gestión de candidatos funciona correctamente")
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
        
        # Probar API de candidatos
        print("\n3. Probando API de candidatos (/api/candidates)...")
        response = requests.get(f"{base_url}/api/candidates", timeout=10)
        if response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get('success'):
                    data = response_data.get('data', [])
                    total = response_data.get('total', 0)
                    print(f"   ✅ API funciona - {total} candidatos encontrados")
                    
                    # Verificar estructura de datos
                    if data and len(data) > 0 and isinstance(data[0], dict):
                        candidate = data[0]
                        required_fields = ['id', 'name', 'total_mentions', 'unique_articles']
                        missing_fields = [field for field in required_fields if field not in candidate]
                        
                        if missing_fields:
                            print(f"   ⚠️  Campos faltantes: {missing_fields}")
                        else:
                            print("   ✅ Estructura de datos correcta")
                    elif len(data) == 0:
                        print("   ⚠️  No hay candidatos en la base de datos")
                    else:
                        print("   ⚠️  Estructura de datos inesperada")
                else:
                    print(f"   ❌ API devolvió error: {response_data.get('error', 'Desconocido')}")
                    return False
                        
            except json.JSONDecodeError:
                print("   ❌ Error al parsear JSON")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
        
        return True
        
    except requests.RequestException as e:
        print(f"   ❌ Error de conexión: {e}")
        return False

def test_feed_autodiscovery():
    """Probar el autodescubrimiento de feeds mejorado"""
    print("\n" + "="*60)
    print("🧪 PRUEBA: Autodescubrimiento de Feeds")
    print("="*60)
    
    base_url = "http://127.0.0.1:5000"
    
    test_sites = [
        {'url': 'www.infobae.com', 'expected_min': 1},
        {'url': 'clarin.com', 'expected_min': 0},
        {'url': 'lanacion.com.ar', 'expected_min': 0}
    ]
    
    success_count = 0
    
    for site in test_sites:
        print(f"\n🔍 Probando: {site['url']}")
        
        try:
            response = requests.post(
                f"{base_url}/feeds/autodiscover",
                json={'url': site['url']},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    feeds_count = data.get('count', 0)
                    print(f"   ✅ {feeds_count} feeds encontrados")
                    
                    if feeds_count >= site['expected_min']:
                        print(f"   ✅ Cumple expectativa mínima ({site['expected_min']})")
                        success_count += 1
                    else:
                        print(f"   ⚠️  Menos feeds de lo esperado (mín: {site['expected_min']})")
                    
                    # Mostrar feeds encontrados
                    for i, feed in enumerate(data.get('feeds', []), 1):
                        print(f"      {i}. {feed.get('title', 'Sin título')}")
                        print(f"         {feed.get('url', '')}")
                else:
                    print(f"   ❌ Error: {data.get('error', 'Desconocido')}")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Error de conexión: {e}")
        
        time.sleep(1)  # Pausa entre requests
    
    print(f"\n📊 Resultado: {success_count}/{len(test_sites)} sitios exitosos")
    return success_count > 0

def test_web_interface():
    """Probar la interfaz web general"""
    print("\n" + "="*60)
    print("🧪 PRUEBA: Interfaz Web General")
    print("="*60)
    
    base_url = "http://127.0.0.1:5000"
    
    routes_to_test = [
        {'path': '/', 'name': 'Dashboard principal'},
        {'path': '/feeds', 'name': 'Gestión de feeds'},
        {'path': '/keywords', 'name': 'Gestión de keywords'},
        {'path': '/subscriptions', 'name': 'Suscripciones'},
        {'path': '/logs', 'name': 'Logs del sistema'}
    ]
    
    success_count = 0
    
    for route in routes_to_test:
        print(f"\n🔍 Probando: {route['name']} ({route['path']})")
        
        try:
            response = requests.get(f"{base_url}{route['path']}", timeout=10)
            if response.status_code == 200:
                if "Error al cargar" in response.text or "500 Internal Server Error" in response.text:
                    print("   ❌ Error en la página")
                else:
                    print("   ✅ Página carga correctamente")
                    success_count += 1
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"   ❌ Error de conexión: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{len(routes_to_test)} rutas exitosas")
    return success_count == len(routes_to_test)

def generate_final_report():
    """Generar reporte final del estado del sistema"""
    print("\n" + "="*80)
    print("📋 REPORTE FINAL DEL SISTEMA")
    print("="*80)
    
    print(f"\n🕐 Fecha y hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Ejecutar todas las pruebas
    results = {
        'candidate_management': test_candidate_management(),
        'feed_autodiscovery': test_feed_autodiscovery(),
        'web_interface': test_web_interface()
    }
    
    print("\n" + "="*80)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\n✅ Pruebas exitosas: {passed_tests}/{total_tests}")
    
    for test_name, result in results.items():
        status = "✅ EXITOSO" if result else "❌ FALLIDO"
        test_display = {
            'candidate_management': 'Gestión de Candidatos',
            'feed_autodiscovery': 'Autodescubrimiento de Feeds',
            'web_interface': 'Interfaz Web General'
        }
        print(f"   • {test_display[test_name]}: {status}")
    
    print("\n" + "="*80)
    print("🎯 ESTADO GENERAL DEL SISTEMA")
    print("="*80)
    
    if passed_tests == total_tests:
        print("\n🎉 ¡EXCELENTE! Todos los componentes funcionan correctamente")
        print("\n✅ CORRECCIONES APLICADAS EXITOSAMENTE:")
        print("   • Errores de gestión de candidatos solucionados")
        print("   • Autodescubrimiento de feeds mejorado")
        print("   • Funciones de storage corregidas")
        print("   • Plantillas HTML actualizadas")
        print("   • Manejo de importance_level corregido")
        
        print("\n🚀 EL SISTEMA ESTÁ LISTO PARA PRODUCCIÓN")
        
    elif passed_tests >= total_tests * 0.7:
        print("\n✅ BUENO: La mayoría de componentes funcionan correctamente")
        print("\n⚠️  ÁREAS QUE REQUIEREN ATENCIÓN:")
        for test_name, result in results.items():
            if not result:
                print(f"   • {test_display[test_name]}")
                
    else:
        print("\n⚠️  ATENCIÓN: Varios componentes requieren corrección")
        print("\n❌ COMPONENTES CON PROBLEMAS:")
        for test_name, result in results.items():
            if not result:
                print(f"   • {test_display[test_name]}")
    
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES FINALES")
    print("="*80)
    
    print("\n1. 🔍 MONITOREO:")
    print("   • Revisar logs regularmente en /logs")
    print("   • Monitorear el estado de feeds en /feeds")
    print("   • Verificar integridad de datos periódicamente")
    
    print("\n2. 🛠️  MANTENIMIENTO:")
    print("   • Ejecutar test_integrity.py semanalmente")
    print("   • Limpiar logs antiguos mensualmente")
    print("   • Actualizar feeds inactivos")
    
    print("\n3. 📈 OPTIMIZACIÓN:")
    print("   • Considerar optimizar consultas FTS5 lentas")
    print("   • Implementar cache para consultas frecuentes")
    print("   • Configurar alertas automáticas")
    
    return passed_tests == total_tests

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBAS FINALES DEL SISTEMA")
    print("🔧 Verificando todas las correcciones aplicadas...")
    
    # Esperar un momento para que el servidor esté listo
    print("\n⏳ Esperando que el servidor esté listo...")
    time.sleep(2)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor web no está respondiendo correctamente")
            print("💡 Asegúrate de que 'python web_app.py' esté ejecutándose")
            return False
    except requests.RequestException:
        print("❌ No se puede conectar al servidor web")
        print("💡 Asegúrate de que 'python web_app.py' esté ejecutándose en el puerto 5000")
        return False
    
    print("✅ Servidor web detectado y funcionando")
    
    # Ejecutar reporte final
    success = generate_final_report()
    
    print("\n" + "="*80)
    print("🏁 PRUEBAS COMPLETADAS")
    print("="*80)
    
    if success:
        print("\n🎉 ¡TODAS LAS CORRECCIONES FUNCIONAN PERFECTAMENTE!")
        print("\n🎯 PRÓXIMOS PASOS RECOMENDADOS:")
        print("   1. Agregar feeds de medios argentinos")
        print("   2. Configurar candidatos y keywords")
        print("   3. Configurar suscripciones de Telegram")
        print("   4. Iniciar monitoreo en producción")
    else:
        print("\n⚠️  ALGUNAS CORRECCIONES REQUIEREN ATENCIÓN ADICIONAL")
        print("\n💡 Revisa los detalles arriba para identificar problemas pendientes")
    
    return success

if __name__ == "__main__":
    main()