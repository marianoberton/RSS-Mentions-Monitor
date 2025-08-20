#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_important_hits

print("=== VERIFICACIÓN DE MENCIONES IMPORTANTES ===")
print("Buscando menciones de Oscar Liberman y Gustavo Coria...\n")

# Obtener menciones de las últimas 24 horas
hits = get_important_hits(24)

print(f"Menciones de Liberman en últimas 24h: {len(hits['liberman'])}")
print(f"Menciones de Coria en últimas 24h: {len(hits['coria'])}")

if hits['liberman']:
    print("\n📰 DETALLES LIBERMAN:")
    for i, hit in enumerate(hits['liberman'], 1):
        print(f"{i}. {hit['title']} ({hit['site']})")
        print(f"   Link: {hit['link']}")
        print(f"   Keyword: {hit['keyword']} (en {hit['where_found']})")
        print(f"   Fecha: {hit['published_utc']}")
        print()

if hits['coria']:
    print("\n📰 DETALLES CORIA:")
    for i, hit in enumerate(hits['coria'], 1):
        print(f"{i}. {hit['title']} ({hit['site']})")
        print(f"   Link: {hit['link']}")
        print(f"   Keyword: {hit['keyword']} (en {hit['where_found']})")
        print(f"   Fecha: {hit['published_utc']}")
        print()

if not hits['liberman'] and not hits['coria']:
    print("\n❌ No se encontraron menciones de Liberman o Coria en las últimas 24 horas.")
    print("Esto podría explicar por qué no recibiste la notificación.")

print("\n=== VERIFICACIÓN COMPLETADA ===")