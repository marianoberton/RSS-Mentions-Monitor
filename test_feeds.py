#!/usr/bin/env python3
from app.storage import get_db_connection

def test_feeds():
    conn = get_db_connection()
    
    # Verificar tabla de feed_state
    feeds_count = conn.execute('SELECT COUNT(*) FROM feed_state').fetchone()[0]
    print(f'Total feeds configurados: {feeds_count}')
    
    # Verificar feeds habilitados
    enabled_feeds = conn.execute('SELECT COUNT(*) FROM feed_state WHERE is_enabled = 1').fetchone()[0]
    print(f'Feeds habilitados: {enabled_feeds}')
    
    # Mostrar información de feeds
    feeds_info = conn.execute('''
        SELECT name, error_count, last_success_utc, next_run_at, is_enabled
        FROM feed_state
        ORDER BY name
    ''').fetchall()
    
    print('\nInformación de feeds:')
    for row in feeds_info:
        status = "Habilitado" if row[4] else "Deshabilitado"
        print(f'Feed: {row[0]}, Status: {status}, Errores: {row[1]}, Último éxito: {row[2]}')
    
    # Verificar artículos por sitio
    articles_by_site = conn.execute('''
        SELECT site, COUNT(*) as count
        FROM articles
        GROUP BY site
        ORDER BY count DESC
        LIMIT 10
    ''').fetchall()
    
    print('\nArtículos por sitio (top 10):')
    for row in articles_by_site:
        print(f'{row[0]}: {row[1]} artículos')
    
    # Verificar artículos recientes (últimas 24 horas)
    recent_articles = conn.execute('''
        SELECT COUNT(*) 
        FROM articles 
        WHERE datetime(inserted_utc) > datetime('now', '-1 day')
    ''').fetchone()[0]
    print(f'\nArtículos insertados en las últimas 24 horas: {recent_articles}')
    
    # Verificar procesamiento de contenido
    processed_articles = conn.execute('SELECT COUNT(*) FROM articles WHERE content_processed = 1').fetchone()[0]
    total_articles = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    processing_rate = (processed_articles / total_articles * 100) if total_articles > 0 else 0
    print(f'Artículos procesados: {processed_articles}/{total_articles} ({processing_rate:.1f}%)')
    
    conn.close()

if __name__ == '__main__':
    test_feeds()