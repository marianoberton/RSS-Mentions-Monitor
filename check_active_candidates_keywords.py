#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection

def check_active_candidates_and_keywords():
    """Verificar candidatos activos y sus palabras clave"""
    print("=== Verificación de Candidatos Activos y Palabras Clave ===")
    
    conn = get_db_connection()
    
    # 1. Obtener todos los candidatos activos
    cursor = conn.execute("""
        SELECT id, name, full_name, political_party, is_active
        FROM candidates 
        WHERE is_active = 1
        ORDER BY name
    """)
    active_candidates = cursor.fetchall()
    
    print(f"\n📊 Total de candidatos activos: {len(active_candidates)}")
    print("\n👥 Candidatos activos:")
    
    candidates_with_keywords = []
    candidates_without_keywords = []
    
    for candidate in active_candidates:
        candidate_id, name, full_name, party, is_active = candidate
        print(f"\n  🔹 {name} (ID: {candidate_id})")
        print(f"     Partido: {party}")
        if full_name and full_name != name:
            print(f"     Nombre completo: {full_name}")
        
        # Obtener keywords para este candidato
        cursor = conn.execute("""
            SELECT keyword, is_active
            FROM candidate_keywords 
            WHERE candidate_id = ?
            ORDER BY keyword
        """, (candidate_id,))
        keywords = cursor.fetchall()
        
        active_keywords = [kw[0] for kw in keywords if kw[1] == 1]
        inactive_keywords = [kw[0] for kw in keywords if kw[1] == 0]
        
        if active_keywords:
            print(f"     ✅ Palabras clave activas ({len(active_keywords)}): {', '.join(active_keywords)}")
            candidates_with_keywords.append((candidate_id, name, active_keywords))
        else:
            print(f"     ❌ Sin palabras clave activas")
            candidates_without_keywords.append((candidate_id, name))
            
        if inactive_keywords:
            print(f"     ⚠️ Palabras clave inactivas ({len(inactive_keywords)}): {', '.join(inactive_keywords)}")
    
    # 2. Resumen
    print(f"\n📈 RESUMEN:")
    print(f"  • Candidatos con palabras clave: {len(candidates_with_keywords)}")
    print(f"  • Candidatos sin palabras clave: {len(candidates_without_keywords)}")
    
    if candidates_without_keywords:
        print(f"\n⚠️ CANDIDATOS SIN PALABRAS CLAVE:")
        for candidate_id, name in candidates_without_keywords:
            print(f"  - {name} (ID: {candidate_id})")
    
    # 3. Verificar todas las palabras clave activas en el sistema
    cursor = conn.execute("""
        SELECT ck.keyword, c.name, c.id
        FROM candidate_keywords ck
        JOIN candidates c ON ck.candidate_id = c.id
        WHERE ck.is_active = 1 AND c.is_active = 1
        ORDER BY ck.keyword
    """)
    all_active_keywords = cursor.fetchall()
    
    print(f"\n🔍 TODAS LAS PALABRAS CLAVE ACTIVAS ({len(all_active_keywords)}):")
    current_keyword = None
    for keyword, candidate_name, candidate_id in all_active_keywords:
        if keyword != current_keyword:
            print(f"\n  📝 '{keyword}':")
            current_keyword = keyword
        print(f"     → {candidate_name} (ID: {candidate_id})")
    
    conn.close()
    
    return {
        'total_active_candidates': len(active_candidates),
        'candidates_with_keywords': len(candidates_with_keywords),
        'candidates_without_keywords': len(candidates_without_keywords),
        'total_active_keywords': len(all_active_keywords),
        'candidates_needing_keywords': candidates_without_keywords
    }

if __name__ == "__main__":
    result = check_active_candidates_and_keywords()
    
    if result['candidates_without_keywords'] > 0:
        print(f"\n🚨 ACCIÓN REQUERIDA: {result['candidates_without_keywords']} candidatos necesitan palabras clave")
    else:
        print(f"\n✅ ESTADO ÓPTIMO: Todos los candidatos activos tienen palabras clave")