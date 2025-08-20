#!/usr/bin/env python3

from app.feeds import get_enabled_feeds
from app.storage import get_db_connection

print("Feeds habilitados:")
feeds = get_enabled_feeds()
for feed in feeds:
    print(f"- {feed['name']}")

print(f"\nTotal: {len(feeds)} feeds habilitados")

# Verificar qué feeds tienen artículos sin procesar
print("\nFeeds con artículos sin procesar:")
conn = get_db_connection()
cursor = conn.execute("""
    SELECT site, COUNT(*) as count 
    FROM articles 
    WHERE content_processed = 0 
    GROUP BY site 
    ORDER BY count DESC
""")

unprocessed_feeds = cursor.fetchall()
for site, count in unprocessed_feeds:
    enabled = any(feed['name'] == site for feed in feeds)
    status = "✅ HABILITADO" if enabled else "❌ DESHABILITADO"
    print(f"- {site}: {count} artículos - {status}")

conn.close()