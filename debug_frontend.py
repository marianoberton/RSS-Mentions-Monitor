#!/usr/bin/env python3
"""
Script de debug para verificar el frontend y JavaScript del formulario de candidatos.
"""

import requests
import re
from bs4 import BeautifulSoup

def check_html_structure():
    """Verificar la estructura HTML del formulario"""
    print("=== VERIFICACIÓN DE ESTRUCTURA HTML ===")
    
    try:
        response = requests.get("http://localhost:5000/candidates/manage", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error al cargar la página: {response.status_code}")
            return
            
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verificar elementos clave del formulario
        elements_to_check = [
            ('addCandidateModal', 'Modal de agregar candidato'),
            ('legislative_position', 'Select de cargo político'),
            ('electoral_section', 'Select de sección electoral'),
            ('alliance_id', 'Select de alianza electoral'),
            ('edit_legislative_position', 'Select de cargo político (editar)'),
            ('edit_electoral_section', 'Select de sección electoral (editar)'),
            ('edit_alliance_id', 'Select de alianza electoral (editar)')
        ]
        
        for element_id, description in elements_to_check:
            element = soup.find(id=element_id)
            if element:
                print(f"✅ {description}: Encontrado")
                
                # Si es un select, verificar opciones
                if element.name == 'select':
                    options = element.find_all('option')
                    print(f"   - Opciones iniciales: {len(options)}")
                    for i, option in enumerate(options[:3]):
                        print(f"     {i+1}. {option.get_text().strip()}")
            else:
                print(f"❌ {description}: NO encontrado")
        
        # Verificar JavaScript
        print("\n=== VERIFICACIÓN DE JAVASCRIPT ===")
        
        js_functions = [
            'loadElectoralData',
            'DOMContentLoaded',
            'fetch\(\'/api/political-positions\'\)',
            'fetch\(\'/api/electoral-sections\'\)'
        ]
        
        for func in js_functions:
            if re.search(func, html_content):
                print(f"✅ {func}: Encontrado")
            else:
                print(f"❌ {func}: NO encontrado")
        
        # Verificar si loadElectoralData se llama en DOMContentLoaded
        dom_content_pattern = r'DOMContentLoaded.*?loadElectoralData\(\)'
        if re.search(dom_content_pattern, html_content, re.DOTALL):
            print("✅ loadElectoralData() se llama en DOMContentLoaded")
        else:
            print("❌ loadElectoralData() NO se llama en DOMContentLoaded")
            
        # Buscar posibles errores en el JavaScript
        print("\n=== ANÁLISIS DE JAVASCRIPT ===")
        
        # Extraer todo el JavaScript de la página
        script_tags = soup.find_all('script')
        js_content = ''
        for script in script_tags:
            if script.string:
                js_content += script.string + '\n'
        
        # Verificar estructura de loadElectoralData
        if 'function loadElectoralData()' in js_content:
            print("✅ Función loadElectoralData definida")
            
            # Verificar que se llame a las APIs correctas
            if "fetch('/api/political-positions')" in js_content:
                print("✅ Llamada a API de cargos políticos")
            else:
                print("❌ NO se llama a API de cargos políticos")
                
            if "fetch('/api/electoral-sections')" in js_content:
                print("✅ Llamada a API de secciones electorales")
            else:
                print("❌ NO se llama a API de secciones electorales")
        else:
            print("❌ Función loadElectoralData NO definida")
            
    except Exception as e:
        print(f"❌ Error verificando HTML: {e}")

def generate_test_javascript():
    """Generar código JavaScript para probar en la consola del navegador"""
    print("\n=== CÓDIGO JAVASCRIPT PARA PROBAR EN CONSOLA ===")
    print("Copia y pega este código en la consola del navegador (F12 -> Console):")
    print("\n" + "="*60)
    
    test_js = '''
// Test 1: Verificar que los elementos existen
console.log('=== TEST 1: Verificar elementos ===');
const elements = [
    'legislative_position',
    'electoral_section', 
    'alliance_id',
    'edit_legislative_position',
    'edit_electoral_section',
    'edit_alliance_id'
];

elements.forEach(id => {
    const element = document.getElementById(id);
    console.log(`${id}: ${element ? '✅ Encontrado' : '❌ NO encontrado'}`);
    if (element && element.tagName === 'SELECT') {
        console.log(`  - Opciones: ${element.options.length}`);
    }
});

// Test 2: Verificar que loadElectoralData existe
console.log('\n=== TEST 2: Verificar función ===');
console.log(`loadElectoralData: ${typeof loadElectoralData !== 'undefined' ? '✅ Definida' : '❌ NO definida'}`);

// Test 3: Ejecutar loadElectoralData manualmente
console.log('\n=== TEST 3: Ejecutar función ===');
if (typeof loadElectoralData !== 'undefined') {
    console.log('Ejecutando loadElectoralData()...');
    loadElectoralData();
} else {
    console.log('❌ No se puede ejecutar loadElectoralData');
}

// Test 4: Probar APIs directamente
console.log('\n=== TEST 4: Probar APIs ===');
fetch('/api/political-positions')
    .then(response => response.json())
    .then(data => console.log('API political-positions:', data))
    .catch(error => console.error('Error political-positions:', error));

fetch('/api/electoral-sections')
    .then(response => response.json())
    .then(data => console.log('API electoral-sections:', data))
    .catch(error => console.error('Error electoral-sections:', error));
'''
    
    print(test_js)
    print("="*60)
    print("\nDespués de ejecutar el código, revisa los resultados en la consola.")

def main():
    print("🔍 SCRIPT DE DEBUG FRONTEND - FORMULARIO DE CANDIDATOS")
    print("=" * 60)
    
    check_html_structure()
    generate_test_javascript()
    
    print("\n" + "=" * 60)
    print("✅ Debug frontend completado")
    print("\nPasos siguientes:")
    print("1. Ejecutar el código JavaScript en la consola del navegador")
    print("2. Verificar si hay errores en la consola")
    print("3. Comprobar si las opciones aparecen después de ejecutar loadElectoralData()")

if __name__ == "__main__":
    main()