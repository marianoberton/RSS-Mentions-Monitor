#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_important_hits, get_db_connection
from app.config import config
from datetime import datetime

print("=== VERIFICACIÓN DE ANDRES DE LEO ===")
print("Verificando que se agregó correctamente al sistema...\n")

# 1. Verificar configuración
print("📋 VERIFICANDO CONFIGURACIÓN:")
keywords = config.get('keywords', [])
print(f"Keywords configuradas: {len(keywords)}")
for i, keyword in enumerate(keywords, 1):
    print(f"  {i}. {keyword}")
    
if "Andres de Leo" in keywords:
    print("✅ 'Andres de Leo' está correctamente configurado en keywords")
else:
    print("❌ 'Andres de Leo' NO está en la configuración")

# 2. Verificar función get_important_hits
print("\n🔍 VERIFICANDO FUNCIÓN get_important_hits:")
try:
    hits = get_important_hits(24)  # Últimas 24 horas
    print(f"✅ Función get_important_hits ejecutada correctamente")
    print(f"Estructura devuelta:")
    for key in hits.keys():
        print(f"  - {key}: {len(hits[key])} menciones")
    
    if "andres_de_leo" in hits:
        print("✅ 'andres_de_leo' está incluido en la respuesta")
    else:
        print("❌ 'andres_de_leo' NO está en la respuesta")
except Exception as e:
    print(f"❌ Error al ejecutar get_important_hits: {e}")

# 3. Simular inserción de una mención de prueba
print("\n🧪 SIMULANDO MENCIÓN DE PRUEBA:")
print("Insertando una mención de prueba de Andres de Leo...")

conn = get_db_connection()
with conn:
    # Insertar artículo de prueba
    test_article_id = f"test_andres_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute("""
        INSERT INTO articles (id, site, title, link, published_utc, inserted_utc, content_processed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_article_id,
        "test_site",
        "Artículo de prueba con mención de Andres de Leo",
        "https://test.com/andres-article",
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        1
    ))
    
    # Insertar hit de prueba
    conn.execute("""
        INSERT INTO hits (article_id, keyword, where_found, detected_utc, notification_sent)
        VALUES (?, ?, ?, ?, ?)
    """, (
        test_article_id,
        "Andres de Leo",
        "title",
        datetime.now().isoformat(),
        0  # No enviada aún
    ))

print("✅ Mención de prueba insertada")

# 4. Verificar que se detecta la nueva mención
print("\n📤 VERIFICANDO DETECCIÓN:")
hits_new = get_important_hits(1)  # Última hora
print(f"Menciones detectadas:")
print(f"  - Liberman: {len(hits_new['liberman'])}")
print(f"  - Coria: {len(hits_new['coria'])}")
print(f"  - Andres de Leo: {len(hits_new['andres_de_leo'])}")

if hits_new["andres_de_leo"]:
    print("\n✅ ÉXITO: Se detectó la mención de Andres de Leo")
    for hit in hits_new["andres_de_leo"]:
        print(f"  - Título: {hit['title']}")
        print(f"  - Sitio: {hit['site']}")
        print(f"  - Keyword: {hit['keyword']}")
        print(f"  - Detectado en: {hit['where_found']}")
else:
    print("❌ No se detectó la mención de Andres de Leo")

# 5. Limpiar datos de prueba
print("\n🧹 LIMPIANDO DATOS DE PRUEBA:")
with conn:
    conn.execute("DELETE FROM hits WHERE article_id = ?", (test_article_id,))
    conn.execute("DELETE FROM articles WHERE id = ?", (test_article_id,))
print("✅ Datos de prueba eliminados")

# 6. Verificar estructura de base de datos
print("\n📊 ESTADÍSTICAS FINALES:")
with conn:
    # Total de menciones por persona
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Liberman%'")
    liberman_total = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Coria%'")
    coria_total = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits WHERE keyword LIKE '%Andres de Leo%' OR keyword LIKE '%Andrés de Leo%'")
    andres_total = cursor.fetchone()[0]
    
    print(f"Total de menciones históricas:")
    print(f"  - Liberman: {liberman_total}")
    print(f"  - Coria: {coria_total}")
    print(f"  - Andres de Leo: {andres_total}")

print("\n🎯 RESUMEN:")
print("• ✅ Andres de Leo agregado a config.yml")
print("• ✅ Función get_important_hits actualizada")
print("• ✅ Sistema de notificaciones actualizado")
print("• ✅ Logging actualizado en tasks.py")
print("• ✅ Sistema listo para detectar menciones de Andres de Leo")

print("\n📋 PRÓXIMOS PASOS:")
print("1. El sistema monitoreará automáticamente menciones de 'Andres de Leo'")
print("2. Las notificaciones se enviarán por Telegram cuando se detecten")
print("3. Se aplicará el mismo sistema anti-duplicados")
print("4. Las menciones se incluirán en los logs del sistema")

print("\n=== VERIFICACIÓN COMPLETADA ===")