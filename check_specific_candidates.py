#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_db_connection

def check_specific_candidates():
    """Verificar keywords de candidatos específicos sin menciones."""
    conn = get_db_connection()
    
    print("=== KEYWORDS DE CANDIDATOS SIN MENCIONES ===")
    
    # Candidatos que no tienen menciones
    candidates_without_hits = ['Diego Santilli', 'Facundo Manes', 'Sergio Massa']
    
    for candidate_name in candidates_without_hits:
        print(f"\n{candidate_name}:")
        cursor = conn.execute("""
            SELECT ck.keyword, ck.is_active, ck.created_utc
            FROM candidates c 
            JOIN candidate_keywords ck ON c.id = ck.candidate_id
            WHERE c.name = ?
            ORDER BY ck.keyword
        """, (candidate_name,))
        
        keywords = cursor.fetchall()
        if keywords:
            for row in keywords:
                keyword, is_active, created_utc = row
                status = "ACTIVA" if is_active else "INACTIVA"
                print(f"  - '{keyword}' ({status}) - Creada: {created_utc}")
        else:
            print(f"  - Sin keywords configuradas")
    
    # Verificar si el sistema de monitoreo está usando estas keywords
    print("\n=== VERIFICACIÓN DEL SISTEMA DE MONITOREO ===")
    
    # Verificar qué keywords están siendo monitoreadas actualmente
    cursor = conn.execute("""
        SELECT DISTINCT ck.keyword
        FROM candidate_keywords ck
        WHERE ck.is_active = 1
        ORDER BY ck.keyword
    """)
    
    active_keywords = [row[0] for row in cursor.fetchall()]
    print(f"\nKeywords activas en el sistema: {len(active_keywords)}")
    for keyword in active_keywords:
        print(f"  - '{keyword}'")
    
    # Verificar si hay artículos recientes que podrían contener estas keywords
    print("\n=== BÚSQUEDA MANUAL EN ARTÍCULOS RECIENTES ===")
    
    test_keywords = ['Diego Santilli', 'Santilli', 'Facundo Manes', 'Manes']
    
    for keyword in test_keywords:
        cursor = conn.execute("""
            SELECT COUNT(*) 
            FROM articles 
            WHERE (title LIKE ? OR full_content LIKE ?)
            AND inserted_utc > datetime('now', '-7 days')
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        count = cursor.fetchone()[0]
        print(f"Artículos de los últimos 7 días que contienen '{keyword}': {count}")
        
        if count > 0:
            # Mostrar algunos ejemplos
            cursor = conn.execute("""
                SELECT title, site, inserted_utc
                FROM articles 
                WHERE (title LIKE ? OR full_content LIKE ?)
                AND inserted_utc > datetime('now', '-7 days')
                LIMIT 3
            """, (f'%{keyword}%', f'%{keyword}%'))
            
            examples = cursor.fetchall()
            for title, site, inserted_utc in examples:
                print(f"  → {title[:60]}... ({site}) - {inserted_utc}")
    
    conn.close()

if __name__ == "__main__":
    check_specific_candidates()