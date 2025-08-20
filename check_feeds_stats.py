#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

def check_feeds_stats():
    conn = sqlite3.connect('data/mentions.db')
    cursor = conn.cursor()
    
    print("=== ESTADÍSTICAS DE FEEDS ===")
    print()
    
    # Verificar artículos por feed
    print("📰 ARTÍCULOS POR FEED:")
    cursor.execute("""
        SELECT site, COUNT(*) as count
        FROM articles 
        GROUP BY site 
        ORDER BY count DESC
    """)
    
    articles_by_feed = cursor.fetchall()
    total_articles = 0
    
    for site, count in articles_by_feed:
        print(f"  {site}: {count} artículos")
        total_articles += count
    
    print(f"\n📊 TOTAL DE ARTÍCULOS: {total_articles}")
    print()
    
    # Verificar hits/menciones por feed
    print("🎯 MENCIONES POR FEED:")
    cursor.execute("""
        SELECT a.site, COUNT(h.id) as hits_count
        FROM articles a
        LEFT JOIN hits h ON a.id = h.article_id
        GROUP BY a.site
        ORDER BY hits_count DESC
    """)
    
    hits_by_feed = cursor.fetchall()
    total_hits = 0
    
    for site, hits_count in hits_by_feed:
        print(f"  {site}: {hits_count} menciones")
        total_hits += hits_count
    
    print(f"\n🎯 TOTAL DE MENCIONES: {total_hits}")
    print()
    
    # Verificar artículos recientes (últimos 7 días)
    print("📅 ARTÍCULOS RECIENTES (últimos 7 días):")
    seven_days_ago = datetime.now() - timedelta(days=7)
    cursor.execute("""
        SELECT site, COUNT(*) as count
        FROM articles 
        WHERE published_utc >= ?
        GROUP BY site 
        ORDER BY count DESC
    """, (seven_days_ago.isoformat(),))
    
    recent_articles = cursor.fetchall()
    total_recent = 0
    
    for site, count in recent_articles:
        print(f"  {site}: {count} artículos")
        total_recent += count
    
    print(f"\n📊 TOTAL RECIENTES: {total_recent}")
    print()
    
    # Verificar feeds configurados vs feeds con datos
    print("⚙️ ESTADO DE FEEDS:")
    
    # Leer feeds del config
    import yaml
    try:
        with open('config.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if isinstance(config['feeds'], dict):
            configured_feeds = list(config['feeds'].keys())
        else:
            configured_feeds = [feed['name'] if isinstance(feed, dict) else str(feed) for feed in config['feeds']]
        feeds_with_data = [site for site, count in articles_by_feed if count > 0]
        
        print(f"  Feeds configurados: {len(configured_feeds)}")
        print(f"  Feeds con datos: {len(feeds_with_data)}")
        
        missing_feeds = set(configured_feeds) - set(feeds_with_data)
        if missing_feeds:
            print(f"  ⚠️ Feeds sin datos: {', '.join(missing_feeds)}")
        
    except Exception as e:
        print(f"  Error leyendo config: {e}")
    
    print()
    
    # Verificar últimas menciones
    print("🔍 ÚLTIMAS 10 MENCIONES:")
    cursor.execute("""
        SELECT a.site, a.title, h.keyword, h.where_found, a.published_utc
        FROM hits h
        JOIN articles a ON h.article_id = a.id
        ORDER BY a.published_utc DESC
        LIMIT 10
    """)
    
    recent_hits = cursor.fetchall()
    
    for site, title, keyword, where_found, published_utc in recent_hits:
        print(f"  📰 {site} | {keyword} en {where_found} | {title[:50]}...")
        print(f"     📅 {published_utc}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_feeds_stats()