#!/usr/bin/env python3
from app.storage import get_db_connection

def test_search():
    conn = get_db_connection()
    
    # Verificar tablas FTS
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%fts%'").fetchall()
    print('Tablas FTS:', [t[0] for t in tables])
    
    # Verificar artículos con menciones
    articles = conn.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    print(f'Total artículos: {articles}')
    
    # Buscar menciones de "Milei"
    milei_mentions = conn.execute("SELECT COUNT(*) FROM articles WHERE title LIKE '%Milei%' OR full_content LIKE '%Milei%'").fetchone()[0]
    print(f'Menciones de Milei: {milei_mentions}')
    
    # Verificar si existe tabla articles_fts
    fts_exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'").fetchone()
    if fts_exists:
        print('Tabla articles_fts existe')
        # Probar búsqueda FTS
        try:
            fts_results = conn.execute("SELECT COUNT(*) FROM articles_fts WHERE articles_fts MATCH 'Milei'").fetchone()[0]
            print(f'Resultados FTS para Milei: {fts_results}')
        except Exception as e:
            print(f'Error en búsqueda FTS: {e}')
    else:
        print('Tabla articles_fts NO existe')
    
    # Verificar algunos artículos recientes
    recent_articles = conn.execute('''
        SELECT title, published_utc, site 
        FROM articles 
        ORDER BY published_utc DESC 
        LIMIT 5
    ''').fetchall()
    
    print('\nArtículos recientes:')
    for row in recent_articles:
        print(f'Sitio: {row[2]}, Fecha: {row[1]}, Título: {row[0][:80]}...')
    
    conn.close()

if __name__ == '__main__':
    test_search()