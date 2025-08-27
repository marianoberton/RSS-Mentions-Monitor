#!/usr/bin/env python3
"""
Script para verificar hits en la base de datos.
"""

from app.storage import get_db_connection

def check_hits():
    print("=== VERIFICACIÓN DE HITS ===")
    
    conn = get_db_connection()
    
    # 1. Verificar hits para Diego Santilli
    print("\n1. HITS PARA 'Diego Santilli':")
    cursor = conn.execute("SELECT * FROM hits WHERE keyword = 'Diego Santilli' ORDER BY detected_utc DESC LIMIT 5")
    hits = cursor.fetchall()
    
    if hits:
        for hit in hits:
            print(f"  ID: {hit['id']}, Article: {hit['article_id']}, Person: {hit['person_id']}, Where: {hit['where_found']}, Date: {hit['detected_utc']}")
    else:
        print("  No se encontraron hits para 'Diego Santilli'")
    
    # 2. Verificar hits para el artículo específico
    article_id = 'c1cc876db4499c5b2f981c530513639f'
    print(f"\n2. HITS PARA ARTÍCULO {article_id}:")
    cursor = conn.execute("SELECT * FROM hits WHERE article_id = ? ORDER BY detected_utc DESC", (article_id,))
    article_hits = cursor.fetchall()
    
    if article_hits:
        for hit in article_hits:
            print(f"  ID: {hit['id']}, Keyword: {hit['keyword']}, Person: {hit['person_id']}, Where: {hit['where_found']}, Date: {hit['detected_utc']}")
    else:
        print(f"  No se encontraron hits para el artículo {article_id}")
    
    # 3. Verificar total de hits
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_hits = cursor.fetchone()[0]
    print(f"\n3. TOTAL DE HITS EN LA BASE DE DATOS: {total_hits}")
    
    # 4. Verificar últimos 5 hits
    print("\n4. ÚLTIMOS 5 HITS:")
    cursor = conn.execute("SELECT * FROM hits ORDER BY detected_utc DESC LIMIT 5")
    recent_hits = cursor.fetchall()
    
    for hit in recent_hits:
        print(f"  ID: {hit['id']}, Keyword: {hit['keyword']}, Article: {hit['article_id']}, Person: {hit['person_id']}, Date: {hit['detected_utc']}")
    
    # 5. Verificar candidate_id para Diego Santilli
    print("\n5. CANDIDATE_ID PARA 'Diego Santilli':")
    cursor = conn.execute("SELECT candidate_id FROM candidate_keywords WHERE keyword = 'Diego Santilli' AND is_active = 1")
    result = cursor.fetchone()
    
    if result:
        candidate_id = result[0]
        print(f"  Candidate ID: {candidate_id}")
        
        # Verificar hits para este candidate_id
        cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE person_id = ?", (candidate_id,))
        candidate_hits = cursor.fetchone()[0]
        print(f"  Hits para candidate_id {candidate_id}: {candidate_hits}")
    else:
        print("  No se encontró candidate_id para 'Diego Santilli'")
    
    conn.close()
    print("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == '__main__':
    check_hits()