#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection

def test_browser_delete():
    print("=== Prueba de Eliminación desde Navegador ===")
    
    # URL del servidor Flask
    base_url = "http://localhost:5000"
    
    # Primero verificar candidatos activos
    conn = get_db_connection()
    cursor = conn.execute("SELECT id, name FROM candidates WHERE is_active = 1 ORDER BY id")
    active_candidates = cursor.fetchall()
    conn.close()
    
    if not active_candidates:
        print("❌ No hay candidatos activos para eliminar")
        return
    
    print("\n👥 Candidatos activos disponibles:")
    for candidate in active_candidates:
        print(f"  - ID: {candidate[0]} | Nombre: {candidate[1]}")
    
    # Seleccionar el primer candidato para eliminar
    candidate_to_delete = active_candidates[0]
    candidate_id = candidate_to_delete[0]
    candidate_name = candidate_to_delete[1]
    
    print(f"\n🎯 Intentando eliminar: {candidate_name} (ID: {candidate_id})")
    
    # Simular la petición POST que hace el navegador
    delete_url = f"{base_url}/candidates/{candidate_id}/delete"
    
    try:
        # Crear una sesión para mantener cookies
        session = requests.Session()
        
        # Primero hacer GET a la página de gestión para obtener cookies/sesión
        print("\n📡 Obteniendo sesión...")
        manage_response = session.get(f"{base_url}/candidates/manage")
        print(f"Status de página de gestión: {manage_response.status_code}")
        
        # Ahora hacer POST para eliminar
        print(f"\n🗑️ Enviando POST a: {delete_url}")
        
        # Simular exactamente lo que hace el JavaScript
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': f'{base_url}/candidates/manage',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # El JavaScript no envía datos en el cuerpo, solo hace POST
        delete_response = session.post(delete_url, headers=headers, allow_redirects=False)
        
        print(f"Status de eliminación: {delete_response.status_code}")
        print(f"Headers de respuesta: {dict(delete_response.headers)}")
        
        if delete_response.status_code == 302:
            print(f"✅ Redirección exitosa a: {delete_response.headers.get('Location')}")
        elif delete_response.status_code == 200:
            print("✅ Respuesta exitosa (sin redirección)")
        else:
            print(f"⚠️ Status inesperado: {delete_response.status_code}")
            print(f"Contenido: {delete_response.text[:500]}")
        
        # Verificar si el candidato fue eliminado
        print("\n🔍 Verificando eliminación...")
        conn = get_db_connection()
        cursor = conn.execute("SELECT is_active FROM candidates WHERE id = ?", (candidate_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 0:
            print(f"✅ {candidate_name} fue eliminado exitosamente")
        elif result and result[0] == 1:
            print(f"❌ {candidate_name} sigue activo - eliminación falló")
        else:
            print(f"❌ No se encontró el candidato {candidate_id}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor Flask")
        print("   Asegúrate de que el servidor esté ejecutándose en http://localhost:5000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_browser_delete()