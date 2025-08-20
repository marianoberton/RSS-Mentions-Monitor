#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks import hourly_summary
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=== PRUEBA DE RESUMEN HORARIO ===")
print("Ejecutando resumen horario manualmente...\n")

try:
    hourly_summary()
    print("\n✅ Resumen horario ejecutado exitosamente")
    print("Si había menciones de Liberman o Coria, deberías haber recibido notificaciones.")
except Exception as e:
    print(f"\n❌ Error al ejecutar resumen horario: {e}")
    logger.error(f"Error en resumen horario: {e}", exc_info=True)

print("\n=== PRUEBA COMPLETADA ===")