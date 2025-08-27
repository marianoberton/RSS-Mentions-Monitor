#!/usr/bin/env python3
"""
Script de debug para verificar el estado de las APIs y base de datos
que alimentan el formulario de candidatos.
"""

import sqlite3
import requests
import json
from app.config import config
from app.storage import get_db_connection

def check_database_tables():
    """Verificar que las tablas necesarias existan y tengan datos"""
    print("=== VERIFICACIÓN DE BASE DE DATOS ===")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar tablas
        tables_to_check = [
            'electoral_alliances',
            'political_positions', 
            'electoral_sections',
            'candidates'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} registros")
                
                # Mostrar algunos ejemplos
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                for i, row in enumerate(rows, 1):
                    print(f"   {i}. {dict(row)}")
                    
            except sqlite3.Error as e:
                print(f"❌ {table}: ERROR - {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")

def test_api_endpoints():
    """Probar los endpoints de la API"""
    print("\n=== VERIFICACIÓN DE ENDPOINTS API ===")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/political-positions",
        "/api/electoral-sections", 
        "/api/alliances"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"\nProbando: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando a {endpoint}: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ Error decodificando JSON de {endpoint}: {e}")

def check_web_app_routes():
    """Verificar que las rutas del web app estén funcionando"""
    print("\n=== VERIFICACIÓN DE RUTAS WEB ===")
    
    base_url = "http://localhost:5000"
    routes = [
        "/candidates/manage",
        "/candidates"
    ]
    
    for route in routes:
        try:
            url = base_url + route
            print(f"\nProbando: {url}")
            
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Página carga correctamente")
                # Verificar si contiene elementos clave
                content = response.text
                if 'addCandidateModal' in content:
                    print("✅ Modal de agregar candidato encontrado")
                if 'loadElectoralData' in content:
                    print("✅ Función loadElectoralData encontrada")
                else:
                    print("❌ Función loadElectoralData NO encontrada")
            else:
                print(f"❌ Error: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando a {route}: {e}")

def check_javascript_console():
    """Simular verificación de errores de JavaScript"""
    print("\n=== VERIFICACIÓN DE JAVASCRIPT ===")
    print("Para verificar errores de JavaScript:")
    print("1. Abrir DevTools (F12) en el navegador")
    print("2. Ir a la pestaña Console")
    print("3. Recargar la página /candidates/manage")
    print("4. Buscar errores relacionados con:")
    print("   - loadElectoralData()")
    print("   - fetch('/api/political-positions')")
    print("   - fetch('/api/electoral-sections')")
    print("   - DOMContentLoaded")

def main():
    print("🔍 SCRIPT DE DEBUG - FORMULARIO DE CANDIDATOS")
    print("=" * 50)
    
    check_database_tables()
    test_api_endpoints()
    check_web_app_routes()
    check_javascript_console()
    
    print("\n" + "=" * 50)
    print("✅ Debug completado")
    print("\nSi las APIs funcionan pero las opciones no aparecen:")
    print("1. Verificar errores en la consola del navegador")
    print("2. Verificar que loadElectoralData() se ejecute")
    print("3. Verificar que los selects tengan los IDs correctos")

if __name__ == "__main__":
    main()