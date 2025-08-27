#!/usr/bin/env python3
"""
Script para corregir errores en la gestión de candidatos:
1. Actualizar get_all_candidates() para incluir estadísticas
2. Corregir get_candidate_stats() para usar candidate_id correctamente
3. Manejar importance_level como string/int apropiadamente
4. Corregir plantillas HTML
"""

import sqlite3
import os
from datetime import datetime

def fix_storage_functions():
    """Corregir las funciones en storage.py"""
    storage_file = "app/storage.py"
    
    # Leer el archivo actual
    with open(storage_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Corregir get_all_candidates para incluir estadísticas
    old_get_all_candidates = '''def get_all_candidates() -> List[Dict[str, Any]]:
    """Obtener todos los candidatos activos."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT id, name, full_name, description, legislative_position, 
                   political_party, electoral_section, district, importance_level, created_utc
            FROM candidates 
            WHERE is_active = 1
            ORDER BY electoral_section, importance_level DESC, name
        """)
        
        candidates = []
        for row in cursor:
            candidates.append({
                "id": row[0],
                "name": row[1],
                "full_name": row[2],
                "description": row[3],
                "legislative_position": row[4],
                "political_party": row[5],
                "electoral_section": row[6],
                "district": row[7],
                "importance_level": row[8],
                "created_utc": row[9]
            })
            
        return candidates
        
    except Exception as e:
        logger.error(f"Error obteniendo todos los candidatos: {e}")
        return []'''
    
    new_get_all_candidates = '''def get_all_candidates() -> List[Dict[str, Any]]:
    """Obtener todos los candidatos activos con estadísticas."""
    conn = get_db_connection()
    
    try:
        cursor = conn.execute("""
            SELECT c.id, c.name, c.full_name, c.description, c.legislative_position, 
                   c.political_party, c.electoral_section, c.district, c.importance_level, 
                   c.created_utc, c.is_active
            FROM candidates c
            WHERE c.is_active = 1
            ORDER BY c.electoral_section, c.importance_level DESC, c.name
        """)
        
        candidates = []
        for row in cursor:
            candidate_id = row[0]
            
            # Obtener estadísticas de menciones para cada candidato
            stats_cursor = conn.execute("""
                SELECT COUNT(*) as total_mentions,
                       COUNT(DISTINCT h.article_id) as unique_articles,
                       MIN(h.detected_utc) as first_mention,
                       MAX(h.detected_utc) as last_mention
                FROM hits h
                JOIN candidate_keywords ck ON h.keyword = ck.keyword
                WHERE ck.candidate_id = ? AND ck.is_active = 1
            """, (candidate_id,))
            
            stats = stats_cursor.fetchone()
            total_mentions = stats[0] if stats[0] else 0
            unique_articles = stats[1] if stats[1] else 0
            first_mention = stats[2]
            last_mention = stats[3]
            
            # Convertir importance_level a string para compatibilidad con templates
            importance_map = {1: 'low', 2: 'medium', 3: 'high'}
            importance_str = importance_map.get(row[8], 'low')
            
            candidates.append({
                "id": candidate_id,
                "name": row[1],
                "full_name": row[2],
                "description": row[3],
                "legislative_position": row[4],
                "political_party": row[5],
                "electoral_section": row[6],
                "district": row[7],
                "importance_level": importance_str,
                "importance_level_int": row[8],
                "created_utc": row[9],
                "is_active": row[10],
                "total_mentions": total_mentions,
                "unique_articles": unique_articles,
                "first_mention": datetime.fromisoformat(first_mention) if first_mention else None,
                "last_mention": datetime.fromisoformat(last_mention) if last_mention else None
            })
            
        return candidates
        
    except Exception as e:
        logger.error(f"Error obteniendo todos los candidatos: {e}")
        return []'''
    
    # 2. Corregir get_candidate_stats para usar candidate_id correctamente
    old_get_candidate_stats = '''        # Total de hits para este candidato
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits WHERE person_id = ?
        """, (candidate_id,))
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Artículos únicos
        cursor = conn.execute("""
            SELECT COUNT(DISTINCT article_id) FROM hits WHERE person_id = ?
        """, (candidate_id,))
        stats["unique_articles"] = cursor.fetchone()[0]'''
    
    new_get_candidate_stats = '''        # Total de hits para este candidato
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
        """, (candidate_id,))
        stats["total_hits"] = cursor.fetchone()[0]
        
        # Artículos únicos
        cursor = conn.execute("""
            SELECT COUNT(DISTINCT h.article_id) FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
        """, (candidate_id,))
        stats["unique_articles"] = cursor.fetchone()[0]'''
    
    # Aplicar los cambios
    content = content.replace(old_get_all_candidates, new_get_all_candidates)
    content = content.replace(old_get_candidate_stats, new_get_candidate_stats)
    
    # También corregir otras consultas en get_candidate_stats
    old_recent_hits = '''        # Hits recientes (últimas X horas)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits 
            WHERE person_id = ? AND datetime(detected_utc) >= datetime('now', '-{} hours')
        """.format(hours), (candidate_id,))'''
    
    new_recent_hits = '''        # Hits recientes (últimas X horas)
        cursor = conn.execute("""
            SELECT COUNT(*) FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1 
            AND datetime(h.detected_utc) >= datetime('now', '-{} hours')
        """.format(hours), (candidate_id,))'''
    
    content = content.replace(old_recent_hits, new_recent_hits)
    
    # Corregir primera y última mención
    old_mentions = '''        # Primera y última mención
        cursor = conn.execute("""
            SELECT MIN(detected_utc) as first_mention, MAX(detected_utc) as last_mention
            FROM hits WHERE person_id = ?
        """, (candidate_id,))'''
    
    new_mentions = '''        # Primera y última mención
        cursor = conn.execute("""
            SELECT MIN(h.detected_utc) as first_mention, MAX(h.detected_utc) as last_mention
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
        """, (candidate_id,))'''
    
    content = content.replace(old_mentions, new_mentions)
    
    # Corregir breakdown por keyword
    old_breakdown = '''        # Breakdown por keyword
        cursor = conn.execute("""
            SELECT keyword, COUNT(*) as count
            FROM hits 
            WHERE person_id = ?
            GROUP BY keyword
            ORDER BY count DESC
        """, (candidate_id,))'''
    
    new_breakdown = '''        # Breakdown por keyword
        cursor = conn.execute("""
            SELECT h.keyword, COUNT(*) as count
            FROM hits h
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            GROUP BY h.keyword
            ORDER BY count DESC
        """, (candidate_id,))'''
    
    content = content.replace(old_breakdown, new_breakdown)
    
    # Corregir artículos recientes
    old_articles = '''        # Artículos recientes
        cursor = conn.execute("""
            SELECT DISTINCT a.title, a.site, a.link, h.detected_utc
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            WHERE h.person_id = ?
            ORDER BY h.detected_utc DESC
            LIMIT 10
        """, (candidate_id,))'''
    
    new_articles = '''        # Artículos recientes
        cursor = conn.execute("""
            SELECT DISTINCT a.title, a.site, a.link, h.detected_utc
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            JOIN candidate_keywords ck ON h.keyword = ck.keyword
            WHERE ck.candidate_id = ? AND ck.is_active = 1
            ORDER BY h.detected_utc DESC
            LIMIT 10
        """, (candidate_id,))'''
    
    content = content.replace(old_articles, new_articles)
    
    # Escribir el archivo corregido
    with open(storage_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Funciones de storage.py corregidas")

def fix_web_app():
    """Corregir el manejo de importance_level en web_app.py"""
    web_app_file = "web_app.py"
    
    with open(web_app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corregir el manejo de importance_level para aceptar strings
    old_importance = '''        importance_level = request.form.get('importance_level', 1)
        keywords = request.form.get('keywords', '').split(',')
        
        if not name or not political_party or not legislative_position:
            flash('El nombre, partido político y cargo legislativo son requeridos', 'error')
            return redirect(url_for('manage_candidates'))
        
        from app.storage import create_candidate, add_candidate_keyword
        
        # Crear candidato usando la función de storage
        candidate_id = create_candidate(
            name=name,
            political_party=political_party,
            electoral_section=electoral_section,
            legislative_position=legislative_position,
            full_name=full_name,
            description=description,
            district=district,
            list_number=int(list_number) if list_number else None,
            list_position=int(list_position) if list_position else None,
            importance_level=int(importance_level)
        )'''
    
    new_importance = '''        importance_level = request.form.get('importance_level', 'medium')
        keywords = request.form.get('keywords', '').split(',')
        
        if not name or not political_party or not legislative_position:
            flash('El nombre, partido político y cargo legislativo son requeridos', 'error')
            return redirect(url_for('manage_candidates'))
        
        # Convertir importance_level de string a int
        importance_map = {'low': 1, 'medium': 2, 'high': 3}
        importance_int = importance_map.get(importance_level, 2)
        
        from app.storage import create_candidate, add_candidate_keyword
        
        # Crear candidato usando la función de storage
        candidate_id = create_candidate(
            name=name,
            political_party=political_party,
            electoral_section=electoral_section,
            legislative_position=legislative_position,
            full_name=full_name,
            description=description,
            district=district,
            list_number=int(list_number) if list_number else None,
            list_position=int(list_position) if list_position else None,
            importance_level=importance_int
        )'''
    
    content = content.replace(old_importance, new_importance)
    
    with open(web_app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ web_app.py corregido")

def fix_templates():
    """Corregir las plantillas HTML"""
    
    # Corregir manage_candidates.html
    manage_template = "templates/manage_candidates.html"
    
    with open(manage_template, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Corregir el uso de .title() en importance_level
    old_importance_display = '''                                        <span class="badge bg-{{ 'danger' if candidate.importance_level == 'high' else 'warning' if candidate.importance_level == 'medium' else 'secondary' }}">
                                            {{ candidate.importance_level.title() }}
                                        </span>'''
    
    new_importance_display = '''                                        <span class="badge bg-{{ 'danger' if candidate.importance_level == 'high' else 'warning' if candidate.importance_level == 'medium' else 'secondary' }}">
                                            {{ candidate.importance_level|title }}
                                        </span>'''
    
    content = content.replace(old_importance_display, new_importance_display)
    
    with open(manage_template, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Plantilla manage_candidates.html corregida")

def main():
    """Ejecutar todas las correcciones"""
    print("🔧 Iniciando corrección de errores en gestión de candidatos...")
    
    try:
        fix_storage_functions()
        fix_web_app()
        fix_templates()
        
        print("\n✅ Todas las correcciones aplicadas exitosamente!")
        print("\n📋 Errores corregidos:")
        print("   1. get_all_candidates() ahora incluye total_mentions y unique_articles")
        print("   2. get_candidate_stats() usa candidate_id correctamente")
        print("   3. importance_level se maneja como string en formularios")
        print("   4. Plantillas HTML corregidas para evitar errores de atributos")
        print("\n🔄 Reinicia el servidor web para aplicar los cambios")
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()