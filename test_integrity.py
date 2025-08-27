#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testing de integridad del sistema RSS Mentions Monitor
Verifica consistencia de datos y relaciones entre tablas
"""

import sqlite3
from datetime import datetime, timedelta
import re

def test_referential_integrity():
    """Verifica integridad referencial entre tablas"""
    print("=== TESTING DE INTEGRIDAD REFERENCIAL ===")
    
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Test 1: Verificar que todos los candidate_id en subscriptions existen en candidates
    cursor.execute("""
        SELECT cs.id, cs.candidate_id 
        FROM candidate_subscriptions cs 
        LEFT JOIN candidates c ON cs.candidate_id = c.id 
        WHERE c.id IS NULL
    """)
    orphaned_subscriptions = cursor.fetchall()
    
    if orphaned_subscriptions:
        issues.append(f"❌ {len(orphaned_subscriptions)} suscripciones huérfanas (candidate_id inexistente)")
        for sub_id, candidate_id in orphaned_subscriptions[:5]:  # Mostrar solo primeros 5
            issues.append(f"   - Suscripción {sub_id} referencia candidato {candidate_id} inexistente")
    else:
        print("✅ Integridad referencial candidate_subscriptions -> candidates: OK")
    
    # Test 2: Verificar que todos los political_position_id en candidates existen
    cursor.execute("""
        SELECT c.id, c.name, c.political_position_id 
        FROM candidates c 
        LEFT JOIN political_positions pp ON c.political_position_id = pp.id 
        WHERE c.political_position_id IS NOT NULL AND pp.id IS NULL
    """)
    orphaned_candidates = cursor.fetchall()
    
    if orphaned_candidates:
        issues.append(f"❌ {len(orphaned_candidates)} candidatos con political_position_id inválido")
        for cand_id, name, pos_id in orphaned_candidates[:5]:
            issues.append(f"   - Candidato {name} (ID: {cand_id}) referencia posición {pos_id} inexistente")
    else:
        print("✅ Integridad referencial candidates -> political_positions: OK")
    
    # Test 3: Verificar que todos los electoral_section_id en candidates existen
    cursor.execute("""
        SELECT c.id, c.name, c.electoral_section_id 
        FROM candidates c 
        LEFT JOIN electoral_sections es ON c.electoral_section_id = es.id 
        WHERE c.electoral_section_id IS NOT NULL AND es.id IS NULL
    """)
    orphaned_electoral = cursor.fetchall()
    
    if orphaned_electoral:
        issues.append(f"❌ {len(orphaned_electoral)} candidatos con electoral_section_id inválido")
        for cand_id, name, sect_id in orphaned_electoral[:5]:
            issues.append(f"   - Candidato {name} (ID: {cand_id}) referencia sección {sect_id} inexistente")
    else:
        print("✅ Integridad referencial candidates -> electoral_sections: OK")
    
    conn.close()
    return issues

def test_data_consistency():
    """Verifica consistencia de datos"""
    print("\n=== TESTING DE CONSISTENCIA DE DATOS ===")
    
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Test 1: Verificar URLs duplicadas en articles
    cursor.execute("""
        SELECT canonical_url, COUNT(*) as count 
        FROM articles 
        WHERE canonical_url IS NOT NULL 
        GROUP BY canonical_url 
        HAVING COUNT(*) > 1
    """)
    duplicate_urls = cursor.fetchall()
    
    if duplicate_urls:
        total_duplicates = sum(count - 1 for _, count in duplicate_urls)
        issues.append(f"⚠️ {len(duplicate_urls)} URLs duplicadas ({total_duplicates} artículos duplicados)")
        for url, count in duplicate_urls[:3]:
            issues.append(f"   - {url}: {count} copias")
    else:
        print("✅ No hay URLs duplicadas en articles")
    
    # Test 2: Verificar content_hash duplicados
    cursor.execute("""
        SELECT content_hash, COUNT(*) as count 
        FROM articles 
        WHERE content_hash IS NOT NULL 
        GROUP BY content_hash 
        HAVING COUNT(*) > 1
    """)
    duplicate_hashes = cursor.fetchall()
    
    if duplicate_hashes:
        total_hash_duplicates = sum(count - 1 for _, count in duplicate_hashes)
        issues.append(f"⚠️ {len(duplicate_hashes)} content_hash duplicados ({total_hash_duplicates} artículos)")
    else:
        print("✅ No hay content_hash duplicados")
    
    # Test 3: Verificar fechas inconsistentes
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles 
        WHERE published_utc > inserted_utc
    """)
    future_articles = cursor.fetchone()[0]
    
    if future_articles > 0:
        issues.append(f"⚠️ {future_articles} artículos con fecha de publicación posterior a inserción")
    else:
        print("✅ Fechas de artículos consistentes")
    
    # Test 4: Verificar artículos sin contenido procesado
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles 
        WHERE (content_processed IS NULL OR content_processed = '') 
        AND full_content IS NOT NULL
    """)
    unprocessed_articles = cursor.fetchone()[0]
    
    if unprocessed_articles > 0:
        issues.append(f"⚠️ {unprocessed_articles} artículos sin procesar (tienen full_content pero no content_processed)")
    else:
        print("✅ Todos los artículos con contenido están procesados")
    
    # Test 5: Verificar feeds sin última ejecución exitosa
    cursor.execute("""
        SELECT COUNT(*) 
        FROM feed_state 
        WHERE is_enabled = 1 AND last_success_utc IS NULL
    """)
    feeds_never_success = cursor.fetchone()[0]
    
    if feeds_never_success > 0:
        issues.append(f"⚠️ {feeds_never_success} feeds habilitados que nunca tuvieron éxito")
    else:
        print("✅ Todos los feeds habilitados han tenido al menos una ejecución exitosa")
    
    conn.close()
    return issues

def test_fts_consistency():
    """Verifica consistencia de índices FTS5"""
    print("\n=== TESTING DE CONSISTENCIA FTS5 ===")
    
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Test 1: Verificar que articles_fts tiene el mismo número de registros que articles
    cursor.execute("SELECT COUNT(*) FROM articles")
    articles_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles_fts")
    fts_count = cursor.fetchone()[0]
    
    if articles_count != fts_count:
        issues.append(f"❌ Desincronización FTS: {articles_count} artículos vs {fts_count} en FTS")
    else:
        print(f"✅ FTS sincronizado: {articles_count} registros en ambas tablas")
    
    # Test 2: Verificar que no hay registros FTS huérfanos
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles_fts af 
        LEFT JOIN articles a ON af.rowid = a.id 
        WHERE a.id IS NULL
    """)
    orphaned_fts = cursor.fetchone()[0]
    
    if orphaned_fts > 0:
        issues.append(f"❌ {orphaned_fts} registros FTS huérfanos (sin artículo correspondiente)")
    else:
        print("✅ No hay registros FTS huérfanos")
    
    # Test 3: Verificar que artículos recientes están en FTS
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles a 
        LEFT JOIN articles_fts af ON a.id = af.rowid 
        WHERE a.inserted_utc > datetime('now', '-1 day') AND af.rowid IS NULL
    """)
    missing_recent_fts = cursor.fetchone()[0]
    
    if missing_recent_fts > 0:
        issues.append(f"❌ {missing_recent_fts} artículos recientes no están en FTS")
    else:
        print("✅ Todos los artículos recientes están indexados en FTS")
    
    conn.close()
    return issues

def test_business_logic_integrity():
    """Verifica integridad de lógica de negocio"""
    print("\n=== TESTING DE LÓGICA DE NEGOCIO ===")
    
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    issues = []
    
    # Test 1: Verificar que no hay candidatos duplicados por nombre
    cursor.execute("""
        SELECT name, COUNT(*) as count 
        FROM candidates 
        GROUP BY LOWER(TRIM(name)) 
        HAVING COUNT(*) > 1
    """)
    duplicate_candidates = cursor.fetchall()
    
    if duplicate_candidates:
        issues.append(f"⚠️ {len(duplicate_candidates)} nombres de candidatos duplicados")
        for name, count in duplicate_candidates[:3]:
            issues.append(f"   - '{name}': {count} registros")
    else:
        print("✅ No hay candidatos con nombres duplicados")
    
    # Test 2: Verificar suscripciones activas
    cursor.execute("""
        SELECT COUNT(*) 
        FROM candidate_subscriptions 
        WHERE is_active = 1
    """)
    active_subscriptions = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(DISTINCT candidate_id) 
        FROM candidate_subscriptions 
        WHERE is_active = 1
    """)
    candidates_with_subs = cursor.fetchone()[0]
    
    print(f"✅ {active_subscriptions} suscripciones activas para {candidates_with_subs} candidatos")
    
    # Test 3: Verificar que hay artículos recientes
    cursor.execute("""
        SELECT COUNT(*) 
        FROM articles 
        WHERE inserted_utc > datetime('now', '-7 days')
    """)
    recent_articles = cursor.fetchone()[0]
    
    if recent_articles == 0:
        issues.append("⚠️ No hay artículos insertados en los últimos 7 días")
    else:
        print(f"✅ {recent_articles} artículos insertados en los últimos 7 días")
    
    # Test 4: Verificar feeds activos
    cursor.execute("""
        SELECT COUNT(*) 
        FROM feed_state 
        WHERE is_enabled = 1
    """)
    active_feeds = cursor.fetchone()[0]
    
    if active_feeds == 0:
        issues.append("❌ No hay feeds habilitados")
    else:
        print(f"✅ {active_feeds} feeds habilitados")
    
    conn.close()
    return issues

def generate_integrity_report(ref_issues, data_issues, fts_issues, business_issues):
    """Genera reporte de integridad"""
    print("\n=== REPORTE DE INTEGRIDAD ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_issues = ref_issues + data_issues + fts_issues + business_issues
    
    if not all_issues:
        print("\n🎉 ¡EXCELENTE! No se encontraron problemas de integridad")
        print("✅ Integridad referencial: OK")
        print("✅ Consistencia de datos: OK")
        print("✅ Consistencia FTS5: OK")
        print("✅ Lógica de negocio: OK")
    else:
        print(f"\n⚠️ Se encontraron {len(all_issues)} problemas de integridad:")
        
        if ref_issues:
            print("\n🔗 PROBLEMAS DE INTEGRIDAD REFERENCIAL:")
            for issue in ref_issues:
                print(f"  {issue}")
        
        if data_issues:
            print("\n📊 PROBLEMAS DE CONSISTENCIA DE DATOS:")
            for issue in data_issues:
                print(f"  {issue}")
        
        if fts_issues:
            print("\n🔍 PROBLEMAS DE CONSISTENCIA FTS5:")
            for issue in fts_issues:
                print(f"  {issue}")
        
        if business_issues:
            print("\n💼 PROBLEMAS DE LÓGICA DE NEGOCIO:")
            for issue in business_issues:
                print(f"  {issue}")
        
        print("\n📋 ACCIONES RECOMENDADAS:")
        if any("❌" in issue for issue in all_issues):
            print("  - Revisar y corregir problemas críticos (❌) inmediatamente")
        if any("⚠️" in issue for issue in all_issues):
            print("  - Evaluar y planificar corrección de advertencias (⚠️)")
        if any("FTS" in issue for issue in all_issues):
            print("  - Considerar reconstruir índices FTS5")
        if any("duplicad" in issue.lower() for issue in all_issues):
            print("  - Implementar limpieza de datos duplicados")
    
    return len(all_issues)

def main():
    print("🔍 INICIANDO TESTING DE INTEGRIDAD")
    print("===================================")
    
    try:
        # Test de integridad referencial
        ref_issues = test_referential_integrity()
        
        # Test de consistencia de datos
        data_issues = test_data_consistency()
        
        # Test de consistencia FTS
        fts_issues = test_fts_consistency()
        
        # Test de lógica de negocio
        business_issues = test_business_logic_integrity()
        
        # Generar reporte
        total_issues = generate_integrity_report(ref_issues, data_issues, fts_issues, business_issues)
        
        if total_issues == 0:
            print("\n🎯 RESULTADO: Sistema íntegro y consistente")
        else:
            print(f"\n⚠️ RESULTADO: {total_issues} problemas detectados que requieren atención")
        
    except Exception as e:
        print(f"❌ Error durante testing de integridad: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()