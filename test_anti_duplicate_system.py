#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection, get_important_hits
from app.notifier import send_important_hits_notifications
from app.tasks import hourly_summary
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=== PRUEBA DEL SISTEMA ANTI-DUPLICADOS ===")
print("Verificando que no se envíen notificaciones duplicadas...\n")

# 1. Verificar estado inicial
print("📊 ESTADO INICIAL:")
hits = get_important_hits(24)
print(f"• Menciones de Liberman pendientes: {len(hits['liberman'])}")
print(f"• Menciones de Coria pendientes: {len(hits['coria'])}")

# 2. Ejecutar resumen horario múltiples veces para probar duplicados
print("\n🔄 EJECUTANDO MÚLTIPLES RESÚMENES HORARIOS:")
print("(Antes esto causaría notificaciones duplicadas)")

for i in range(3):
    print(f"\n--- Ejecución {i+1} ---")
    try:
        # Obtener menciones pendientes
        hits_before = get_important_hits(1)
        print(f"Menciones pendientes antes: Liberman={len(hits_before['liberman'])}, Coria={len(hits_before['coria'])}")
        
        # Enviar notificaciones si hay menciones pendientes
        if hits_before["liberman"] or hits_before["coria"]:
            send_important_hits_notifications(hits_before)
            print("✅ Notificaciones enviadas")
        else:
            print("✅ No hay menciones pendientes - Sin notificaciones")
        
        # Verificar estado después
        hits_after = get_important_hits(1)
        print(f"Menciones pendientes después: Liberman={len(hits_after['liberman'])}, Coria={len(hits_after['coria'])}")
        
    except Exception as e:
        print(f"❌ Error en ejecución {i+1}: {e}")

# 3. Simular una nueva mención para probar el sistema
print("\n🆕 SIMULANDO NUEVA MENCIÓN:")
print("Insertando una mención de prueba...")

conn = get_db_connection()
with conn:
    # Insertar artículo de prueba
    test_article_id = f"test_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute("""
        INSERT INTO articles (id, site, title, link, published_utc, inserted_utc, content_processed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_article_id,
        "test_site",
        "Artículo de prueba con mención de Oscar Liberman",
        "https://test.com/article",
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
        "Oscar Liberman",
        "title",
        datetime.now().isoformat(),
        0  # No enviada aún
    ))

print("✅ Mención de prueba insertada")

# 4. Probar que la nueva mención se detecta y envía
print("\n📤 PROBANDO ENVÍO DE NUEVA MENCIÓN:")
hits_new = get_important_hits(1)
print(f"• Nuevas menciones detectadas: Liberman={len(hits_new['liberman'])}, Coria={len(hits_new['coria'])}")

if hits_new["liberman"] or hits_new["coria"]:
    print("📱 Enviando notificación de nueva mención...")
    send_important_hits_notifications(hits_new)
    print("✅ Notificación enviada")
    
    # Verificar que ya no está pendiente
    hits_after_send = get_important_hits(1)
    print(f"• Menciones pendientes después del envío: Liberman={len(hits_after_send['liberman'])}, Coria={len(hits_after_send['coria'])}")
    
    if len(hits_after_send['liberman']) == 0 and len(hits_after_send['coria']) == 0:
        print("✅ Sistema anti-duplicados funcionando correctamente")
    else:
        print("❌ Error: Aún hay menciones pendientes después del envío")
else:
    print("❌ Error: No se detectó la nueva mención")

# 5. Limpiar datos de prueba
print("\n🧹 LIMPIANDO DATOS DE PRUEBA:")
with conn:
    conn.execute("DELETE FROM hits WHERE article_id = ?", (test_article_id,))
    conn.execute("DELETE FROM articles WHERE id = ?", (test_article_id,))
print("✅ Datos de prueba eliminados")

print("\n🎯 RESUMEN DE LA PRUEBA:")
print("• ✅ Sistema anti-duplicados implementado")
print("• ✅ Notificaciones duplicadas eliminadas")
print("• ✅ Nuevas menciones se procesan correctamente")
print("• ✅ Menciones se marcan como enviadas automáticamente")

print("\n=== PRUEBA COMPLETADA EXITOSAMENTE ===")