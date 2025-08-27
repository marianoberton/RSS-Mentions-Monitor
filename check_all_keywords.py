#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection
from datetime import datetime

def check_all_keywords_and_hits():
    """Verificar todas las keywords de candidatos y sus menciones."""
    conn = get_db_connection()
    
    print("=== KEYWORDS POR CANDIDATO Y SUS MENCIONES ===")
    cursor = conn.execute("""
        SELECT c.name, ck.keyword, COUNT(h.id) as hits
        FROM candidates c 
        JOIN candidate_keywords ck ON c.id = ck.candidate_id
        LEFT JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1
        GROUP BY c.name, ck.keyword
        ORDER BY c.name, hits DESC
    """)
    
    current_candidate = None
    total_keywords = 0
    keywords_with_hits = 0
    
    for row in cursor:
        candidate_name, keyword, hits = row
        total_keywords += 1
        if hits > 0:
            keywords_with_hits += 1
            
        if current_candidate != candidate_name:
            if current_candidate is not None:
                print()
            print(f"\n{candidate_name}:")
            current_candidate = candidate_name
        
        status = f"✓ {hits} menciones" if hits > 0 else "✗ 0 menciones"
        print(f"  - {keyword}: {status}")
    
    print(f"\n=== RESUMEN ===")
    print(f"Total keywords: {total_keywords}")
    print(f"Keywords con menciones: {keywords_with_hits}")
    print(f"Keywords sin menciones: {total_keywords - keywords_with_hits}")
    
    print("\n=== KEYWORDS EN HITS QUE NO ESTÁN EN CANDIDATE_KEYWORDS ===")
    cursor = conn.execute("""
        SELECT h.keyword, COUNT(*) as count
        FROM hits h
        LEFT JOIN candidate_keywords ck ON h.keyword = ck.keyword AND ck.is_active = 1
        WHERE ck.keyword IS NULL
        GROUP BY h.keyword
        ORDER BY count DESC
    """)
    
    orphan_keywords = cursor.fetchall()
    if orphan_keywords:
        print("Keywords en hits sin candidato asociado:")
        for row in orphan_keywords:
            keyword, count = row
            print(f"  - {keyword}: {count} menciones")
    else:
        print("Todas las keywords en hits están asociadas a candidatos.")
    
    conn.close()

if __name__ == "__main__":
    check_all_keywords_and_hits()