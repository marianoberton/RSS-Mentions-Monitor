#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import os
from bs4 import BeautifulSoup
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection

def test_real_browser_scenario():
    print("=== Prueba de Escenario Real de Navegador ===")
    
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    try:
        # 1. Obtener la página de gestión de candidatos
        print("\n📄 Obteniendo página de gestión de candidatos...")
        manage_url = f"{base_url}/candidates/manage"
        response = session.get(manage_url)
        
        if response.status_code != 200:
            print(f"❌ Error al obtener página: {response.status_code}")
            return False
        
        print(f"✅ Página obtenida exitosamente (Status: {response.status_code})")
        
        # 2. Parsear HTML para encontrar botones de eliminación
        soup = BeautifulSoup(response.text, 'html.parser')
        delete_buttons = soup.find_all('button', {'onclick': re.compile(r'confirmDelete\(')})
        
        print(f"\n🔍 Botones de eliminación encontrados: {len(delete_buttons)}")
        
        if not delete_buttons:
            print("❌ No se encontraron botones de eliminación en la página")
            return False
        
        # 3. Analizar cada botón de eliminación
        for i, button in enumerate(delete_buttons[:3]):  # Solo los primeros 3
            onclick = button.get('onclick', '')
            print(f"\n🔘 Botón {i+1}: {onclick}")
            
            # Extraer ID y nombre del candidato
            match = re.search(r'confirmDelete\((\d+),\s*[\'"]([^\'"]*)[\'"]*\)', onclick)
            if match:
                candidate_id = int(match.group(1))
                candidate_name = match.group(2)
                print(f"   📋 ID: {candidate_id}, Nombre: '{candidate_name}'")
                
                # 4. Probar eliminación de este candidato
                print(f"\n🎯 Probando eliminación de: {candidate_name} (ID: {candidate_id})")
                
                # Verificar que el candidato existe y está activo
                conn = get_db_connection()
                cursor = conn.execute("SELECT is_active FROM candidates WHERE id = ?", (candidate_id,))
                result = cursor.fetchone()
                conn.close()
                
                if not result:
                    print(f"   ❌ Candidato {candidate_id} no encontrado en BD")
                    continue
                
                if result[0] != 1:
                    print(f"   ⚠️ Candidato {candidate_id} ya está inactivo")
                    continue
                
                print(f"   ✅ Candidato {candidate_id} está activo, procediendo con eliminación")
                
                # 5. Realizar petición POST de eliminación
                delete_url = f"{base_url}/candidates/{candidate_id}/delete"
                print(f"   📡 POST a: {delete_url}")
                
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': manage_url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                delete_response = session.post(delete_url, headers=headers, allow_redirects=False)
                print(f"   📊 Status: {delete_response.status_code}")
                
                if delete_response.status_code == 302:
                    location = delete_response.headers.get('Location', '')
                    print(f"   🔄 Redirección a: {location}")
                    
                    # Verificar eliminación
                    conn = get_db_connection()
                    cursor = conn.execute("SELECT is_active FROM candidates WHERE id = ?", (candidate_id,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result and result[0] == 0:
                        print(f"   ✅ {candidate_name} eliminado exitosamente")
                        return True  # Éxito, salir
                    else:
                        print(f"   ❌ {candidate_name} no fue eliminado")
                        
                elif delete_response.status_code == 200:
                    print(f"   ⚠️ Respuesta 200 (sin redirección)")
                    print(f"   📄 Contenido: {delete_response.text[:200]}...")
                else:
                    print(f"   ❌ Error: Status {delete_response.status_code}")
                    print(f"   📄 Contenido: {delete_response.text[:200]}...")
                
                break  # Solo probar el primer candidato válido
            else:
                print(f"   ❌ No se pudo parsear onclick: {onclick}")
        
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor Flask")
        print("   Asegúrate de que el servidor esté ejecutándose en http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_browser_scenario()
    if success:
        print("\n🎉 Prueba exitosa: La eliminación funciona correctamente")
    else:
        print("\n💥 Prueba fallida: Hay un problema con la eliminación")