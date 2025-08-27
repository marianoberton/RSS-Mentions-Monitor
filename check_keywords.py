#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection
from datetime import datetime

def check_candidate_keywords():
    """Verificar keywords de candidatos y sus menciones."""
    conn = get_db_connection()
    
    print("=== KEYWORDS POR CANDIDATO ===")
    cursor = conn.execute("""
        SELECT c.id, c.name, ck.keyword, ck.is_active
        FROM candidates c 
        LEFT JOIN candidate_keywords ck ON c.id = ck.candidate_id
        WHERE c.is_active = 1
        ORDER BY c.name, ck.keyword
    """)
    
    current_candidate = None
    for row in cursor:
        candidate_id, candidate_name, keyword, is_active = row
        if current_candidate != candidate_name:
            print(f"\n{candidate_name} (ID: {candidate_id}):")
            current_candidate = candidate_name
        
        if keyword:
            status = "ACTIVA" if is_active else "INACTIVA"
            print(f"  - {keyword} ({status})")
        else:
            print(f"  - Sin keywords configuradas")
    
    print("\n=== MENCIONES POR KEYWORD ===")
    cursor = conn.execute("""
        SELECT h.keyword, COUNT(*) as count
        FROM hits h
        GROUP BY h.keyword
        ORDER BY count DESC
    """)
    
    for row in cursor:
        keyword, count = row
        print(f"{keyword}: {count} menciones")
    
    print("\n=== CANDIDATOS CON MENCIONES ===")
    cursor = conn.execute("""
        SELECT c.name, COUNT(h.id) as mentions
        FROM candidates c
        JOIN candidate_keywords ck ON c.id = ck.candidate_id
        JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1
        GROUP BY c.id, c.name
        ORDER BY mentions DESC
    """)
    
    for row in cursor:
        candidate_name, mentions = row
        print(f"{candidate_name}: {mentions} menciones")
    
    print("\n=== TODAS LAS KEYWORDS EN HITS ===")
    cursor = conn.execute("""
        SELECT keyword, COUNT(*) as count
        FROM hits
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 15
    """)
    
    for row in cursor:
        keyword, count = row
        print(f"{keyword}: {count} menciones")
    
    conn.close()

if __name__ == "__main__":
    check_candidate_keywords()