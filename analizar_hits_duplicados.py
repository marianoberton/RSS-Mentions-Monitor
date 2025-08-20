#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from datetime import datetime

print("=== ANÁLISIS DE HITS DUPLICADOS ANDRÉS DE LEO ===")
print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

conn = get_db_connection()

print("🔍 DETALLES DE HITS DUPLICADOS (IDs 959 y 922):")
with conn:
    cursor = conn.execute("""
        SELECT h.id, h.article_id, h.keyword, h.where_found, h.detected_utc, h.notification_sent,
               a.title, a.site, a.link, a.published_utc, a.inserted_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE h.id IN (959, 922)
        ORDER BY h.id
    """)
    
    hits = cursor.fetchall()
    
    for hit in hits:
        print(f"Hit ID: {hit[0]}")
        print(f"Article ID: {hit[1]}")
        print(f"Keyword: {hit[2]}")
        print(f"Where found: {hit[3]}")
        print(f"Detected: {hit[4]}")
        print(f"Notification sent: {hit[5]}")
        print(f"Title: {hit[6]}")
        print(f"Site: {hit[7]}")
        print(f"Link: {hit[8]}")
        print(f"Published: {hit[9]}")
        print(f"Inserted: {hit[10]}")
        print("---")

print("\n📊 ANÁLISIS DE DUPLICACIÓN:")
with conn:
    # Verificar si son del mismo artículo
    cursor = conn.execute("""
        SELECT DISTINCT article_id FROM hits WHERE id IN (959, 922)
    """)
    article_ids = cursor.fetchall()
    
    if len(article_ids) == 1:
        print(f"✅ Ambos hits pertenecen al mismo artículo: {article_ids[0][0]}")
        
        # Buscar todos los hits de este artículo
        cursor = conn.execute("""
            SELECT id, keyword, where_found, detected_utc, notification_sent
            FROM hits 
            WHERE article_id = ?
            ORDER BY detected_utc
        """, (article_ids[0][0],))
        
        all_hits = cursor.fetchall()
        print(f"\n📝 TODOS LOS HITS DE ESTE ARTÍCULO ({len(all_hits)} total):")
        for hit in all_hits:
            status = "✅ ENVIADA" if hit[4] == 1 else "⏳ PENDIENTE"
            print(f"  • ID: {hit[0]} | {hit[1]} | {hit[2]} | {hit[3]} | {status}")
    else:
        print(f"⚠️  Los hits pertenecen a artículos diferentes: {[aid[0] for aid in article_ids]}")

print("\n🔍 BÚSQUEDA DE PATRONES DE DUPLICACIÓN:")
with conn:
    # Buscar otros casos de duplicación para Andrés de Leo
    cursor = conn.execute("""
        SELECT article_id, COUNT(*) as hit_count, GROUP_CONCAT(id) as hit_ids
        FROM hits 
        WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'
        GROUP BY article_id
        HAVING COUNT(*) > 1
        ORDER BY hit_count DESC
    """)
    
    duplicated_articles = cursor.fetchall()
    
    if duplicated_articles:
        print(f"⚠️  Encontrados {len(duplicated_articles)} artículos con hits duplicados:")
        for dup in duplicated_articles:
            print(f"  • Artículo {dup[0]}: {dup[1]} hits (IDs: {dup[2]})")
    else:
        print("✅ No se encontraron otros artículos con hits duplicados")

print("\n🚨 POSIBLES CAUSAS DEL PROBLEMA:")
print("1. El mismo artículo se procesó múltiples veces")
print("2. El keyword 'Andres de Leo' se detectó en diferentes ubicaciones del mismo artículo")
print("3. Problema en la lógica de detección de duplicados durante el procesamiento")
print("4. El artículo apareció en múltiples feeds RSS")

print("\n🔧 VERIFICACIÓN DE TIMESTAMPS:")
with conn:
    cursor = conn.execute("""
        SELECT h.id, h.detected_utc, a.inserted_utc, a.published_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE h.id IN (959, 922)
        ORDER BY h.detected_utc
    """)
    
    timestamps = cursor.fetchall()
    
    print("Comparación de timestamps:")
    for ts in timestamps:
        print(f"  Hit {ts[0]}: Detectado={ts[1]}, Artículo insertado={ts[2]}, Publicado={ts[3]}")

print("\n💡 RECOMENDACIONES:")
print("1. Implementar verificación de duplicados antes de insertar hits")
print("2. Agregar índice único en (article_id, keyword, where_found)")
print("3. Revisar la lógica de procesamiento de artículos")
print("4. Considerar eliminar hits duplicados existentes")

print("\n=== ANÁLISIS COMPLETADO ===")
conn.close()