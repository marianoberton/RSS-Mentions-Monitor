#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_important_hits
from app.notifier import send_important_hits_notifications
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=== PRUEBA DE NOTIFICACIONES IMPORTANTES ===")
print("Enviando notificación de prueba para menciones de Liberman y Coria...\n")

# Obtener menciones de las últimas 24 horas
hits = get_important_hits(24)

print(f"Menciones encontradas:")
print(f"- Liberman: {len(hits['liberman'])}")
print(f"- Coria: {len(hits['coria'])}")

if hits['liberman'] or hits['coria']:
    print("\n📤 Enviando notificaciones...")
    try:
        send_important_hits_notifications(hits)
        print("✅ Notificaciones enviadas exitosamente")
        
        if hits['liberman']:
            print(f"\n📱 Notificaciones de Liberman enviadas: {len(hits['liberman'])}")
            for hit in hits['liberman']:
                print(f"   - {hit['title'][:60]}...")
        
        if hits['coria']:
            print(f"\n📱 Notificaciones de Coria enviadas: {len(hits['coria'])}")
            for hit in hits['coria']:
                print(f"   - {hit['title'][:60]}...")
                
    except Exception as e:
        print(f"❌ Error al enviar notificaciones: {e}")
        logger.error(f"Error en notificaciones: {e}")
else:
    print("\n❌ No hay menciones para enviar notificaciones de prueba.")
    print("Esto es normal si no hay menciones recientes.")

print("\n=== PRUEBA COMPLETADA ===")