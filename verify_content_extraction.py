#!/usr/bin/env python
"""
Script para verificar el estado de extracción de contenido de los artículos.

Este script analiza la base de datos y muestra estadísticas sobre la extracción
de contenido, incluyendo el número de artículos procesados con éxito, los que
fallaron, y la longitud promedio del contenido extraído.

Ejecución: python verify_content_extraction.py [--site sitio.com] [--limit N]
"""

import sqlite3
import logging
import click
from app.config import config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.command()
@click.option('--site', default=None, help='Filtrar por sitio específico (ej: diario3.com.ar)')
@click.option('--limit', default=None, type=int, help='Limitar el número de artículos a mostrar')
@click.option('--show-content', is_flag=True, help='Mostrar una muestra del contenido extraído')
def main(site, limit, show_content):
    # Conectar a la base de datos
    conn = sqlite3.connect(config["SQLITE_PATH"])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Consultar estadísticas generales
    cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as processed,
        SUM(CASE WHEN content_processed = 0 THEN 1 ELSE 0 END) as pending,
        SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors,
        AVG(CASE WHEN content IS NOT NULL THEN LENGTH(content) ELSE 0 END) as avg_length
    FROM articles
    """)
    
    stats = cursor.fetchone()
    
    print("\n===== ESTADÍSTICAS DE EXTRACCIÓN DE CONTENIDO =====")
    print(f"Total de artículos: {stats['total']}")
    print(f"Artículos procesados: {stats['processed']} ({stats['processed']/stats['total']*100 if stats['total'] > 0 else 0:.2f}%)")
    print(f"Artículos pendientes: {stats['pending']}")
    print(f"Artículos con errores: {stats['errors']}")
    print(f"Longitud promedio del contenido: {stats['avg_length']:.2f} caracteres")
    
    # Consultar estadísticas por sitio
    cursor.execute("""
    SELECT 
        site,
        COUNT(*) as total,
        SUM(CASE WHEN content_processed = 1 THEN 1 ELSE 0 END) as processed,
        SUM(CASE WHEN content_processed = 0 THEN 1 ELSE 0 END) as pending,
        AVG(CASE WHEN content IS NOT NULL THEN LENGTH(content) ELSE 0 END) as avg_length
    FROM articles
    GROUP BY site
    ORDER BY total DESC
    """)
    
    sites = cursor.fetchall()
    
    print("\n===== ESTADÍSTICAS POR SITIO =====")
    print(f"{'Sitio':<30} {'Total':<8} {'Procesados':<12} {'Pendientes':<12} {'Long. Promedio':<15}")
    print("-" * 80)
    
    for site_stats in sites:
        processed_percent = site_stats['processed']/site_stats['total']*100 if site_stats['total'] > 0 else 0
        print(f"{site_stats['site']:<30} {site_stats['total']:<8} {site_stats['processed']:<6} ({processed_percent:.1f}%) {site_stats['pending']:<12} {site_stats['avg_length']:.2f}")
    
    # Mostrar artículos específicos si se solicita
    if site or limit:
        query = """
        SELECT id, title, url, site, content_processed, 
               CASE WHEN content IS NULL THEN 0 ELSE LENGTH(content) END as content_length,
               error
        FROM articles
        WHERE 1=1
        """
        
        params = []
        if site:
            query += " AND site LIKE ?"
            params.append(f"%{site}%")
        
        query += " ORDER BY published_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        articles = cursor.fetchall()
        
        print("\n===== DETALLE DE ARTÍCULOS =====")
        for article in articles:
            print(f"\nID: {article['id']}")
            print(f"Título: {article['title']}")
            print(f"URL: {article['url']}")
            print(f"Sitio: {article['site']}")
            print(f"Procesado: {'Sí' if article['content_processed'] else 'No'}")
            print(f"Longitud del contenido: {article['content_length']} caracteres")
            if article['error']:
                print(f"Error: {article['error']}")
            
            # Mostrar muestra del contenido si se solicita
            if show_content and article['content_length'] > 0:
                # Obtener el contenido
                cursor.execute("SELECT content FROM articles WHERE id = ?", (article['id'],))
                content = cursor.fetchone()['content']
                
                # Mostrar los primeros 200 caracteres
                print("\nMuestra del contenido:")
                print("-" * 50)
                print(content[:200] + "..." if len(content) > 200 else content)
                print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    main()