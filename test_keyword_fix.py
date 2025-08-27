#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app.storage import get_all_active_keywords, get_db_connection
from app.tasks import main_task
import logging

# Configurar logging para ver los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_keyword_fix():
    """Probar que el sistema ahora detecte keywords de candidatos."""
    print("=== PRUEBA DE CORRECCIÓN DE KEYWORDS ===")
    
    # 1. Verificar que la nueva función obtiene todas las keywords
    print("\n1. Verificando keywords activas:")
    all_keywords = get_all_active_keywords()
    print(f"Total keywords activas: {len(all_keywords)}")
    
    # Mostrar algunas keywords de candidatos
    candidate_keywords = []
    conn = get_db_connection()
    cursor = conn.execute("""
        SELECT DISTINCT ck.keyword
        FROM candidate_keywords ck
        JOIN candidates c ON ck.candidate_id = c.id
        WHERE ck.is_active = 1 AND c.is_active = 1
        ORDER BY ck.keyword
    """)
    candidate_keywords = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"Keywords de candidatos: {len(candidate_keywords)}")
    for keyword in candidate_keywords[:10]:  # Mostrar las primeras 10
        print(f"  - {keyword}")
    
    # 2. Verificar que las keywords de candidatos están en la lista completa
    print("\n2. Verificando inclusión de keywords de candidatos:")
    missing_keywords = []
    for keyword in candidate_keywords:
        if keyword not in all_keywords:
            missing_keywords.append(keyword)
    
    if missing_keywords:
        print(f"❌ Keywords de candidatos faltantes: {missing_keywords}")
    else:
        print("✅ Todas las keywords de candidatos están incluidas")
    
    # 3. Ejecutar una pasada del sistema de monitoreo
    print("\n3. Ejecutando sistema de monitoreo con keywords corregidas:")
    try:
        main_task()
        print("✅ Sistema de monitoreo ejecutado exitosamente")
    except Exception as e:
        print(f"❌ Error en sistema de monitoreo: {e}")
    
    # 4. Verificar si se detectaron nuevas menciones
    print("\n4. Verificando nuevas menciones detectadas:")
    conn = get_db_connection()
    
    # Contar menciones de candidatos específicos
    test_candidates = ['Diego Santilli', 'Facundo Manes', 'Sergio Massa']
    for candidate_name in test_candidates:
        cursor = conn.execute("""
            SELECT COUNT(h.id)
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            JOIN candidates c ON ck.candidate_id = c.id
            WHERE c.name = ? AND h.detected_utc > datetime('now', '-1 hour')
        """, (candidate_name,))
        
        recent_hits = cursor.fetchone()[0]
        print(f"  {candidate_name}: {recent_hits} menciones en la última hora")
    
    # Verificar menciones totales por keyword de candidatos
    print("\n5. Menciones totales por keyword de candidatos:")
    cursor = conn.execute("""
        SELECT ck.keyword, c.name, COUNT(h.id) as hits
        FROM candidate_keywords ck
        JOIN candidates c ON ck.candidate_id = c.id
        LEFT JOIN hits h ON ck.keyword = h.keyword
        WHERE ck.is_active = 1 AND c.is_active = 1
        GROUP BY ck.keyword, c.name
        ORDER BY hits DESC, c.name
        LIMIT 15
    """)
    
    for row in cursor.fetchall():
        keyword, candidate_name, hits = row
        print(f"  {keyword} ({candidate_name}): {hits} menciones")
    
    conn.close()
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    test_keyword_fix()