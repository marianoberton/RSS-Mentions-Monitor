#!/usr/bin/env python3
"""
Script para debuggear en detalle la función save_article_and_hit.
"""

import sqlite3
from app.storage import get_db_connection
from app.utils import get_utc_now
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_save_hit():
    print("=== DEBUG DE SAVE_ARTICLE_AND_HIT ===")
    
    # Datos de prueba
    article_id = 'c1cc876db4499c5b2f981c530513639f'
    keyword = 'Diego Santilli'
    
    conn = get_db_connection()
    
    # 1. Verificar que el artículo existe
    print("\n1. VERIFICANDO ARTÍCULO:")
    cursor = conn.execute("SELECT id, title, site FROM articles WHERE id = ?", (article_id,))
    article_row = cursor.fetchone()
    
    if article_row:
        print(f"  ✓ Artículo encontrado: {article_row['title']}")
        article = {
            "id": article_row['id'],
            "site": article_row['site'],
            "title": article_row['title'],
            "link": "https://test.com",
            "published_utc": "2025-08-25T01:00:00Z",
            "inserted_utc": "2025-08-25T01:00:00Z"
        }
    else:
        print(f"  ✗ Artículo no encontrado")
        return
    
    # 2. Verificar candidate_keywords
    print("\n2. VERIFICANDO CANDIDATE_KEYWORDS:")
    cursor = conn.execute("SELECT candidate_id FROM candidate_keywords WHERE keyword = ? AND is_active = 1", (keyword,))
    result = cursor.fetchone()
    
    if result:
        candidate_id = result[0]
        print(f"  ✓ Candidate ID encontrado: {candidate_id}")
    else:
        print(f"  ✗ No se encontró candidate_id para '{keyword}'")
        return
    
    # 3. Verificar hits existentes
    print("\n3. VERIFICANDO HITS EXISTENTES:")
    cursor = conn.execute(
        "SELECT id FROM hits WHERE article_id = ? AND person_id = ? AND keyword = ? AND where_found = ?",
        (article_id, candidate_id, keyword, "content")
    )
    existing_hit = cursor.fetchone()
    
    if existing_hit:
        print(f"  ✓ Hit ya existe: ID {existing_hit[0]}")
        return
    else:
        print(f"  ✓ No hay hit existente, se puede crear")
    
    # 4. Crear el hit manualmente
    print("\n4. CREANDO HIT MANUALMENTE:")
    now_utc = get_utc_now()
    
    try:
        cursor = conn.execute(
            "INSERT INTO hits (article_id, person_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?, ?)",
            (article_id, candidate_id, keyword, "content", now_utc.isoformat())
        )
        
        hit_id = cursor.lastrowid
        conn.commit()
        
        print(f"  ✓ Hit creado exitosamente: ID {hit_id}")
        
        # Verificar que se guardó
        cursor = conn.execute("SELECT * FROM hits WHERE id = ?", (hit_id,))
        saved_hit = cursor.fetchone()
        
        if saved_hit:
            print(f"  ✓ Hit verificado en DB: {dict(saved_hit)}")
        else:
            print(f"  ✗ Hit no se encontró después de guardar")
            
    except Exception as e:
        print(f"  ✗ Error creando hit: {e}")
        conn.rollback()
    
    # 5. Verificar hits totales para Diego Santilli
    print("\n5. VERIFICANDO HITS TOTALES PARA DIEGO SANTILLI:")
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword = ?", (keyword,))
    total_hits = cursor.fetchone()[0]
    print(f"  Total hits para '{keyword}': {total_hits}")
    
    # 6. Verificar hits para candidate_id 7
    print("\n6. VERIFICANDO HITS PARA CANDIDATE_ID 7:")
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE person_id = ?", (candidate_id,))
    candidate_hits = cursor.fetchone()[0]
    print(f"  Total hits para candidate_id {candidate_id}: {candidate_hits}")
    
    # 7. Listar todos los hits para este candidate_id
    print("\n7. LISTANDO HITS PARA CANDIDATE_ID 7:")
    cursor = conn.execute("SELECT * FROM hits WHERE person_id = ? ORDER BY detected_utc DESC", (candidate_id,))
    hits = cursor.fetchall()
    
    if hits:
        for hit in hits:
            print(f"  ID: {hit['id']}, Keyword: {hit['keyword']}, Article: {hit['article_id']}, Date: {hit['detected_utc']}")
    else:
        print(f"  No hay hits para candidate_id {candidate_id}")
    
    conn.close()
    print("\n=== DEBUG COMPLETADO ===")

if __name__ == '__main__':
    debug_save_hit()