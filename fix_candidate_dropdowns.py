#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar el problema de opciones faltantes 
en los dropdowns del formulario de candidatos.
"""

import requests
import re
from bs4 import BeautifulSoup
import json

def test_apis():
    """Probar que las APIs funcionen correctamente"""
    print("=== PROBANDO APIS ===")
    
    apis = [
        ('/api/political-positions', 'Cargos políticos'),
        ('/api/electoral-sections', 'Secciones electorales'),
        ('/api/alliances', 'Alianzas electorales')
    ]
    
    all_working = True
    
    for endpoint, name in apis:
        try:
            response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if endpoint == '/api/political-positions':
                    count = len(data.get('positions', []))
                elif endpoint == '/api/electoral-sections':
                    count = len(data.get('sections', []))
                else:
                    count = len(data.get('alliances', []))
                print(f"✅ {name}: {count} elementos")
            else:
                print(f"❌ {name}: Error {response.status_code}")
                all_working = False
        except Exception as e:
            print(f"❌ {name}: Error {e}")
            all_working = False
    
    return all_working

def check_html_structure():
    """Verificar estructura HTML"""
    print("\n=== VERIFICANDO HTML ===")
    
    try:
        response = requests.get("http://localhost:5000/candidates/manage", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error cargando página: {response.status_code}")
            return False
            
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verificar elementos críticos
        critical_elements = [
            'legislative_position',
            'electoral_section',
            'alliance_id'
        ]
        
        all_found = True
        for element_id in critical_elements:
            element = soup.find(id=element_id)
            if element:
                options = element.find_all('option')
                print(f"✅ {element_id}: {len(options)} opciones")
            else:
                print(f"❌ {element_id}: NO encontrado")
                all_found = False
        
        # Verificar JavaScript crítico
        js_checks = [
            ('loadElectoralData', 'Función principal'),
            ('DOMContentLoaded.*loadElectoralData', 'Llamada en DOMContentLoaded')
        ]
        
        for pattern, description in js_checks:
            if re.search(pattern, html_content, re.DOTALL):
                print(f"✅ {description}: Encontrado")
            else:
                print(f"❌ {description}: NO encontrado")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Error verificando HTML: {e}")
        return False

def generate_browser_test():
    """Generar test para ejecutar en el navegador"""
    print("\n=== CÓDIGO PARA PROBAR EN NAVEGADOR ===")
    print("1. Abrir DevTools (F12)")
    print("2. Ir a Console")
    print("3. Pegar y ejecutar este código:")
    print("\n" + "="*50)
    
    browser_code = '''
// Verificar elementos
console.log('=== VERIFICANDO ELEMENTOS ===');
const selects = ['legislative_position', 'electoral_section', 'alliance_id'];
selects.forEach(id => {
    const el = document.getElementById(id);
    console.log(`${id}: ${el ? el.options.length + ' opciones' : 'NO encontrado'}`);
});

// Verificar función
console.log('\n=== VERIFICANDO FUNCIÓN ===');
console.log('loadElectoralData:', typeof loadElectoralData);

// Ejecutar función manualmente
console.log('\n=== EJECUTANDO FUNCIÓN ===');
if (typeof loadElectoralData === 'function') {
    console.log('Ejecutando loadElectoralData()...');
    loadElectoralData();
    
    // Verificar después de 2 segundos
    setTimeout(() => {
        console.log('\n=== RESULTADO DESPUÉS DE 2 SEGUNDOS ===');
        selects.forEach(id => {
            const el = document.getElementById(id);
            if (el) console.log(`${id}: ${el.options.length} opciones`);
        });
    }, 2000);
} else {
    console.log('❌ loadElectoralData no está definida');
}

// Probar APIs directamente
console.log('\n=== PROBANDO APIS ===');
fetch('/api/political-positions')
    .then(r => r.json())
    .then(d => console.log('Political positions:', d.positions?.length || 0))
    .catch(e => console.error('Error political-positions:', e));

fetch('/api/electoral-sections')
    .then(r => r.json())
    .then(d => console.log('Electoral sections:', d.sections?.length || 0))
    .catch(e => console.error('Error electoral-sections:', e));
'''
    
    print(browser_code)
    print("="*50)

def provide_solutions():
    """Proporcionar posibles soluciones"""
    print("\n=== POSIBLES SOLUCIONES ===")
    
    solutions = [
        "1. VERIFICAR CONSOLA DEL NAVEGADOR:",
        "   - Abrir F12 -> Console",
        "   - Buscar errores JavaScript",
        "   - Ejecutar el código de prueba arriba",
        "",
        "2. SI loadElectoralData NO SE EJECUTA:",
        "   - Verificar que esté en DOMContentLoaded",
        "   - Ejecutar manualmente en consola",
        "",
        "3. SI LAS APIS NO RESPONDEN:",
        "   - Verificar que el servidor esté corriendo",
        "   - Revisar logs del servidor",
        "",
        "4. SI HAY ERRORES DE CORS:",
        "   - Verificar configuración de Flask",
        "   - Revisar headers de respuesta",
        "",
        "5. SOLUCIÓN TEMPORAL:",
        "   - Ejecutar loadElectoralData() manualmente",
        "   - Recargar la página",
        "",
        "6. SI NADA FUNCIONA:",
        "   - Revisar manage_candidates.html línea ~950",
        "   - Verificar que loadElectoralData() esté en DOMContentLoaded",
        "   - Comprobar sintaxis JavaScript"
    ]
    
    for solution in solutions:
        print(solution)

def main():
    print("🔧 DIAGNÓSTICO Y SOLUCIÓN - DROPDOWNS DE CANDIDATOS")
    print("=" * 60)
    
    # Paso 1: Probar APIs
    apis_working = test_apis()
    
    # Paso 2: Verificar HTML
    html_ok = check_html_structure()
    
    # Paso 3: Generar test para navegador
    generate_browser_test()
    
    # Paso 4: Proporcionar soluciones
    provide_solutions()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print(f"APIs funcionando: {'✅' if apis_working else '❌'}")
    print(f"HTML correcto: {'✅' if html_ok else '❌'}")
    
    if apis_working and html_ok:
        print("\n🎯 DIAGNÓSTICO: El problema está en el JavaScript del navegador.")
        print("   Ejecuta el código de prueba en la consola del navegador.")
    else:
        print("\n⚠️  DIAGNÓSTICO: Hay problemas en el backend o HTML.")
        print("   Revisa los errores mostrados arriba.")
    
    print("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    main()