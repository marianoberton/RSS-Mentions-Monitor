#!/usr/bin/env python3
"""
Script para probar la eliminación de candidatos desde el frontend
"""

import requests
import sys

def test_delete_candidate(candidate_id):
    """Probar eliminación de candidato"""
    base_url = "http://127.0.0.1:5000"
    delete_url = f"{base_url}/candidates/{candidate_id}/delete"
    
    print(f"Probando eliminación del candidato ID: {candidate_id}")
    print(f"URL: {delete_url}")
    
    try:
        # Hacer petición POST
        response = requests.post(delete_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Eliminación exitosa")
        elif response.status_code == 302:
            print("✅ Redirección exitosa (eliminación completada)")
            print(f"Redirect Location: {response.headers.get('Location', 'No location header')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Probar con un candidato existente (usar ID 14 que debería existir)
    test_delete_candidate(14)