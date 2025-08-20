#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_important_hits, get_db_connection

print("=== VERIFICACIÓN DE MENCIONES HORARIAS ===")
print(f"Hora actual UTC: {datetime.utcnow().isoformat()}")
print(f"Hace 1 hora UTC: {(datetime.utcnow() - timedelta(hours=1)).isoformat()}")
print()

# Verificar menciones de la última hora
hits_1h = get_important_hits(1)
print(f"Menciones en última hora:")
print(f"- Liberman: {len(hits_1h['liberman'])}")
print(f"- Coria: {len(hits_1h['coria'])}")

if hits_1h['liberman']:
    print("\n📰 DETALLES LIBERMAN (última hora):")
    for hit in hits_1h['liberman']:
        print(f"- Detectado: {hit['detected_utc']}")
        print(f"  Título: {hit['title'][:60]}...")
        print(f"  Sitio: {hit['site']}")
        print()

if hits_1h['coria']:
    print("\n📰 DETALLES CORIA (última hora):")
    for hit in hits_1h['coria']:
        print(f"- Detectado: {hit['detected_utc']}")
        print(f"  Título: {hit['title'][:60]}...")
        print(f"  Sitio: {hit['site']}")
        print()

# Verificar todas las menciones de Liberman para entender cuándo se detectó
conn = get_db_connection()
with conn:
    cursor = conn.execute("""
        SELECT h.detected_utc, a.title, a.site, a.published_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        WHERE h.keyword LIKE '%Liberman%'
        ORDER BY h.detected_utc DESC
        LIMIT 5
    """)
    
    all_liberman = cursor.fetchall()
    
print("\n📋 TODAS LAS MENCIONES DE LIBERMAN (últimas 5):")
for hit in all_liberman:
    detected, title, site, published = hit
    print(f"- Detectado: {detected}")
    print(f"  Publicado: {published}")
    print(f"  Título: {title[:60]}...")
    print(f"  Sitio: {site}")
    
    # Calcular diferencia con hora actual
    try:
        detected_dt = datetime.fromisoformat(detected.replace('Z', '+00:00'))
        now_dt = datetime.utcnow().replace(tzinfo=detected_dt.tzinfo)
        diff = now_dt - detected_dt
        print(f"  Hace: {diff.total_seconds()/3600:.1f} horas")
    except:
        print(f"  Error calculando tiempo")
    print()

print("=== VERIFICACIÓN COMPLETADA ===")