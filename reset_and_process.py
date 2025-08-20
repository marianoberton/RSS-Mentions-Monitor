#!/usr/bin/env python
"""
Script para reiniciar la base de datos y procesar todos los artículos nuevamente.

Este script elimina la base de datos actual, crea una nueva, procesa los feeds
y luego procesa todos los artículos utilizando tanto el método tradicional como
Playwright para asegurar la extracción completa del contenido.

Ejecución: python reset_and_process.py
"""

import os
import logging
import sqlite3
import time
import sys
import feedparser
from app.config import config
from app.feeds import get_enabled_feeds
from app.tasks import process_feed
from app.improved_extractor import playwright_available

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_database():
    """Elimina y recrea la base de datos."""
    db_path = config["SQLITE_PATH"]
    
    # Verificar si existen archivos de WAL
    wal_file = f"{db_path}-wal"
    shm_file = f"{db_path}-shm"
    
    # Eliminar archivos de la base de datos si existen
    for file_path in [db_path, wal_file, shm_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
            except Exception as e:
                logger.error(f"Error al eliminar {file_path}: {e}")
    
    # Crear nueva base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas
    cursor.execute("""
    CREATE TABLE articles (
        id TEXT PRIMARY KEY,
        site TEXT NOT NULL,
        title TEXT NOT NULL,
        link TEXT NOT NULL,
        published_utc TEXT NOT NULL,
        inserted_utc TEXT NOT NULL,
        content_processed INTEGER DEFAULT 0,
        full_content TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE hits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id TEXT NOT NULL,
        keyword TEXT NOT NULL,
        where_found TEXT NOT NULL,
        detected_utc TEXT NOT NULL,
        FOREIGN KEY(article_id) REFERENCES articles(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        occurrences INTEGER,
        last_occurrence TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles(id)
    )
    """)
    
    # Habilitar modo WAL
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Base de datos recreada en {db_path}")

def main():
    # Confirmar con el usuario
    print("\n¡ADVERTENCIA! Este script eliminará la base de datos actual y procesará todos los feeds nuevamente.")
    print("Todos los datos existentes se perderán.")
    confirmation = input("¿Estás seguro de que deseas continuar? (s/N): ")
    
    if confirmation.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
        print("Operación cancelada.")
        return
    
    # Verificar si Playwright está disponible
    if not playwright_available:
        print("\nPlaywright no está instalado. Se recomienda instalarlo para una extracción más completa.")
        print("Puedes instalarlo ejecutando: python install_playwright.py")
        confirmation = input("¿Deseas continuar sin Playwright? (s/N): ")
        if confirmation.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("Operación cancelada.")
            return
    
    # Paso 1: Reiniciar la base de datos
    logger.info("Iniciando reinicio de la base de datos...")
    reset_database()
    
    # Paso 2: Procesar todos los feeds
    logger.info("Procesando todos los feeds...")
    feeds = get_enabled_feeds()
    keywords = config.get('keywords', [])
    
    for feed in feeds:
        logger.info(f"Procesando feed: {feed['name']}")
        try:
            process_feed(feed, keywords)
        except Exception as e:
            logger.error(f"Error al procesar feed {feed['name']}: {e}")
            continue
    
    # Paso 3: Procesar artículos con el método tradicional
    logger.info("Procesando artículos con el método tradicional...")
    os.system(f"{sys.executable} background_processor.py")
    
    # Paso 4: Si Playwright está disponible, procesar artículos pendientes con Playwright
    if playwright_available:
        logger.info("Procesando artículos pendientes con Playwright...")
        os.system(f"{sys.executable} process_with_playwright.py")
    
    logger.info("¡Proceso completado! La base de datos ha sido reiniciada y todos los artículos han sido procesados.")
    logger.info("Puedes verificar los resultados ejecutando: python check_processed_content.py")

if __name__ == "__main__":
    main()