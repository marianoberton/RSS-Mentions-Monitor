#!/usr/bin/env python3
"""
Script para probar la funcionalidad de eliminación de candidatos
"""

import requests
import sys
from app.storage import get_db_connection

def test_delete_functionality():
    """Probar la funcionalidad de eliminación de candidatos"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== Test de Funcionalidad de Eliminación de Candidatos ===")
    
    # 1. Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{base_url}/candidates/manage", timeout=5)
        print(f"✓ Servidor respondiendo: {response.status_code}")
    except Exception as e:
        print(f"✗ Error conectando al servidor: {e}")
        return
    
    # 2. Obtener candidatos actuales
    conn = get_db_connection()
    cursor = conn.execute("SELECT id, name, is_active FROM candidates WHERE is_active = 1 ORDER BY id")
    active_candidates = cursor.fetchall()
    conn.close()
    
    print(f"\nCandidatos activos encontrados: {len(active_candidates)}")
    for candidate in active_candidates:
        print(f"  - ID: {candidate[0]}, Nombre: {candidate[1]}")
    
    if not active_candidates:
        print("No hay candidatos activos para probar eliminación")
        return
    
    # 3. Intentar eliminar el último candidato (para no afectar datos importantes)
    test_candidate = active_candidates[-1]
    candidate_id = test_candidate[0]
    candidate_name = test_candidate[1]
    
    print(f"\nProbando eliminación del candidato: {candidate_name} (ID: {candidate_id})")
    
    # 4. Hacer request POST para eliminar
    try:
        delete_url = f"{base_url}/candidates/{candidate_id}/delete"
        print(f"URL de eliminación: {delete_url}")
        
        # Simular el formulario POST
        response = requests.post(delete_url, timeout=10)
        print(f"Respuesta del servidor: {response.status_code}")
        print(f"URL de redirección: {response.url}")
        
        if response.status_code == 200:
            print("✓ Request de eliminación exitoso")
        else:
            print(f"✗ Request falló con código: {response.status_code}")
            print(f"Contenido de respuesta: {response.text[:500]}")
            
    except Exception as e:
        print(f"✗ Error en request de eliminación: {e}")
        return
    
    # 5. Verificar si el candidato fue marcado como inactivo
    conn = get_db_connection()
    cursor = conn.execute("SELECT is_active FROM candidates WHERE id = ?", (candidate_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        is_active = result[0]
        if is_active == 0:
            print(f"✓ Candidato {candidate_name} marcado como inactivo correctamente")
        else:
            print(f"✗ Candidato {candidate_name} sigue activo (is_active = {is_active})")
    else:
        print(f"✗ No se encontró el candidato {candidate_id} en la base de datos")
    
    # 6. Verificar keywords del candidato
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM candidate_keywords WHERE candidate_id = ? AND is_active = 0", (candidate_id,))
    inactive_keywords = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM candidate_keywords WHERE candidate_id = ?", (candidate_id,))
    total_keywords = cursor.fetchone()[0]
    conn.close()
    
    print(f"Keywords del candidato: {inactive_keywords}/{total_keywords} marcadas como inactivas")
    
    print("\n=== Fin del Test ===")

if __name__ == "__main__":
    test_delete_functionality()