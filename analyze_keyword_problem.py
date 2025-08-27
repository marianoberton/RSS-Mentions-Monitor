#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection
from datetime import datetime

def analyze_keyword_problem():
    """Analizar por qué algunas keywords no tienen menciones."""
    conn = get_db_connection()
    
    print("=== ANÁLISIS DEL PROBLEMA DE KEYWORDS ===")
    
    # 1. Ver todas las keywords que SÍ tienen menciones
    print("\n1. KEYWORDS CON MENCIONES:")
    cursor = conn.execute("""
        SELECT DISTINCT h.keyword, COUNT(*) as count
        FROM hits h
        GROUP BY h.keyword
        ORDER BY count DESC
    """)
    
    keywords_with_hits = {}
    for row in cursor:
        keyword, count = row
        keywords_with_hits[keyword] = count
        print(f"  - '{keyword}': {count} menciones")
    
    # 2. Ver todas las keywords de candidatos que NO tienen menciones
    print("\n2. KEYWORDS SIN MENCIONES:")
    cursor = conn.execute("""
        SELECT c.name, ck.keyword
        FROM candidates c
        JOIN candidate_keywords ck ON c.id = ck.candidate_id
        LEFT JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1 AND h.keyword IS NULL
        ORDER BY c.name, ck.keyword
    """)
    
    keywords_without_hits = []
    current_candidate = None
    for row in cursor:
        candidate_name, keyword = row
        keywords_without_hits.append((candidate_name, keyword))
        if current_candidate != candidate_name:
            if current_candidate is not None:
                print()
            print(f"\n{candidate_name}:")
            current_candidate = candidate_name
        print(f"  - '{keyword}'")
    
    # 3. Buscar keywords similares en hits que podrían coincidir
    print("\n3. ANÁLISIS DE KEYWORDS SIMILARES:")
    for candidate_name, keyword in keywords_without_hits:
        # Buscar hits que contengan partes de la keyword
        similar_hits = []
        for hit_keyword in keywords_with_hits.keys():
            # Verificar si la keyword del candidato está contenida en el hit
            if keyword.lower() in hit_keyword.lower() or hit_keyword.lower() in keyword.lower():
                similar_hits.append((hit_keyword, keywords_with_hits[hit_keyword]))
        
        if similar_hits:
            print(f"\n{candidate_name} - '{keyword}':")
            for hit_keyword, count in similar_hits:
                print(f"  → Posible coincidencia: '{hit_keyword}' ({count} menciones)")
    
    # 4. Ver algunos ejemplos de hits para entender el formato
    print("\n4. EJEMPLOS DE HITS:")
    cursor = conn.execute("""
        SELECT keyword, article_id, where_found, detected_utc
        FROM hits
        WHERE keyword IN ('Javier Milei', 'Oscar Liberman', 'Andres de Leo')
        LIMIT 5
    """)
    
    for row in cursor:
        keyword, article_id, where_found, detected_utc = row
        print(f"\nKeyword: '{keyword}'")
        print(f"Article ID: {article_id}")
        print(f"Encontrado en: {where_found}")
        print(f"Detectado: {detected_utc}")
    
    # 5. Verificar si hay problemas de encoding o espacios
    print("\n5. VERIFICACIÓN DE ENCODING Y ESPACIOS:")
    cursor = conn.execute("""
        SELECT DISTINCT keyword, LENGTH(keyword), 
               CASE WHEN keyword != TRIM(keyword) THEN 'CON_ESPACIOS' ELSE 'SIN_ESPACIOS' END as espacios
        FROM candidate_keywords
        WHERE is_active = 1
        ORDER BY keyword
    """)
    
    for row in cursor:
        keyword, length, espacios = row
        print(f"  - '{keyword}' (len={length}, {espacios})")
    
    conn.close()

if __name__ == "__main__":
    analyze_keyword_problem()