#!/usr/bin/env python3
"""
Script para analizar la efectividad del sistema RSS Monitor
y identificar problemas en los métodos de extracción de contenido.
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
from app.config import config
from app.storage import get_db_connection
from app.improved_extractor import extract_article_content_improved, extract_with_retry
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analizar_estadisticas_generales():
    """Analiza las estadísticas generales del sistema."""
    print("\n" + "="*60)
    print("ANÁLISIS DE EFECTIVIDAD DEL SISTEMA RSS MONITOR")
    print("="*60)
    
    conn = get_db_connection()
    
    # Estadísticas generales
    cursor = conn.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    total_mentions = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    unprocessed = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    processed_success = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 2")
    processed_failed = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 3")
    processed_disabled = cursor.fetchone()[0]
    
    # Artículos con contenido del feed vs extraído
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE full_content IS NOT NULL AND full_content != ''")
    with_feed_content = cursor.fetchone()[0]
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"   Total de artículos: {total_articles:,}")
    print(f"   Total de menciones: {total_mentions:,}")
    print(f"   Efectividad general: {(total_mentions/total_articles*100):.1f}%")
    
    print(f"\n🔄 ESTADO DE PROCESAMIENTO:")
    print(f"   Sin procesar: {unprocessed:,} ({unprocessed/total_articles*100:.1f}%)")
    print(f"   Procesados exitosamente: {processed_success:,} ({processed_success/total_articles*100:.1f}%)")
    print(f"   Fallos de extracción: {processed_failed:,} ({processed_failed/total_articles*100:.1f}%)")
    print(f"   Feeds deshabilitados: {processed_disabled:,} ({processed_disabled/total_articles*100:.1f}%)")
    
    print(f"\n📄 CONTENIDO:")
    print(f"   Con contenido del feed: {with_feed_content:,} ({with_feed_content/total_articles*100:.1f}%)")
    print(f"   Requieren extracción: {total_articles - with_feed_content:,} ({(total_articles - with_feed_content)/total_articles*100:.1f}%)")
    
    conn.close()
    return {
        'total_articles': total_articles,
        'total_mentions': total_mentions,
        'unprocessed': unprocessed,
        'processed_failed': processed_failed,
        'with_feed_content': with_feed_content
    }

def analizar_por_feed():
    """Analiza la efectividad por feed."""
    print(f"\n📡 ANÁLISIS POR FEED:")
    
    conn = get_db_connection()
    
    cursor = conn.execute("""
        SELECT 
            site,
            COUNT(*) as total_articles,
            COUNT(CASE WHEN content_processed = 1 THEN 1 END) as processed_success,
            COUNT(CASE WHEN content_processed = 2 THEN 1 END) as processed_failed,
            COUNT(CASE WHEN full_content IS NOT NULL AND full_content != '' THEN 1 END) as with_feed_content,
            COALESCE(h.mentions, 0) as total_mentions
        FROM articles a
        LEFT JOIN (
            SELECT article_id, COUNT(*) as mentions
            FROM hits h2
            JOIN articles a2 ON h2.article_id = a2.id
            GROUP BY a2.site
        ) h ON a.site = h.article_id
        GROUP BY site
        ORDER BY total_articles DESC
    """)
    
    feeds_data = cursor.fetchall()
    
    print(f"{'Feed':<25} {'Artículos':<10} {'Éxito':<8} {'Fallo':<8} {'Feed Content':<12} {'Menciones':<10} {'Efectividad':<12}")
    print("-" * 95)
    
    for feed in feeds_data:
        site, total, success, failed, feed_content, mentions = feed
        effectiveness = (mentions / total * 100) if total > 0 else 0
        success_rate = (success / total * 100) if total > 0 else 0
        
        print(f"{site:<25} {total:<10} {success:<8} {failed:<8} {feed_content:<12} {mentions:<10} {effectiveness:<12.1f}%")
    
    conn.close()
    return feeds_data

def analizar_fallos_extraccion(limit=20):
    """Analiza artículos que fallaron en la extracción."""
    print(f"\n🔍 ANÁLISIS DE FALLOS DE EXTRACCIÓN (últimos {limit}):")
    
    conn = get_db_connection()
    
    cursor = conn.execute("""
        SELECT id, site, title, link, inserted_utc
        FROM articles 
        WHERE content_processed = 2
        ORDER BY inserted_utc DESC
        LIMIT ?
    """, (limit,))
    
    failed_articles = cursor.fetchall()
    
    if not failed_articles:
        print("   ✅ No hay artículos con fallos de extracción recientes.")
        conn.close()
        return []
    
    print(f"   📋 Encontrados {len(failed_articles)} artículos con fallos:")
    
    results = []
    for i, article in enumerate(failed_articles[:10], 1):  # Solo probar los primeros 10
        article_id, site, title, link, inserted_utc = article
        print(f"\n   {i}. {site} - {title[:50]}...")
        print(f"      URL: {link}")
        
        # Intentar extraer contenido ahora
        try:
            print(f"      🔄 Probando extracción...")
            content = extract_with_retry(link, max_retries=2)
            
            if content and len(content) > 100:
                print(f"      ✅ Extracción exitosa: {len(content)} caracteres")
                print(f"      📝 Muestra: {content[:100]}...")
                results.append({
                    'id': article_id,
                    'site': site,
                    'title': title,
                    'link': link,
                    'status': 'success',
                    'content_length': len(content),
                    'content_sample': content[:200]
                })
            else:
                print(f"      ❌ Extracción falló: contenido insuficiente ({len(content) if content else 0} caracteres)")
                results.append({
                    'id': article_id,
                    'site': site,
                    'title': title,
                    'link': link,
                    'status': 'failed',
                    'content_length': len(content) if content else 0
                })
                
        except Exception as e:
            print(f"      ❌ Error en extracción: {str(e)}")
            results.append({
                'id': article_id,
                'site': site,
                'title': title,
                'link': link,
                'status': 'error',
                'error': str(e)
            })
        
        # Pausa para evitar sobrecarga
        if i < len(failed_articles[:10]):
            time.sleep(random.uniform(1, 2))
    
    conn.close()
    return results

def probar_metodos_extraccion(url):
    """Prueba diferentes métodos de extracción en una URL específica."""
    print(f"\n🧪 PROBANDO MÉTODOS DE EXTRACCIÓN:")
    print(f"   URL: {url}")
    
    methods_results = {}
    
    # Método 1: BeautifulSoup básico
    try:
        print(f"\n   1️⃣ Método BeautifulSoup básico:")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar elementos no deseados
        for element in soup.select('script, style, nav, header, footer, iframe'):
            element.decompose()
        
        # Intentar con párrafos
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        methods_results['basic_bs4'] = {
            'length': len(content),
            'sample': content[:200] if content else '',
            'status': 'success' if len(content) > 100 else 'insufficient'
        }
        
        print(f"      📏 Longitud: {len(content)} caracteres")
        print(f"      📝 Muestra: {content[:100]}..." if content else "      ❌ Sin contenido")
        
    except Exception as e:
        methods_results['basic_bs4'] = {'status': 'error', 'error': str(e)}
        print(f"      ❌ Error: {str(e)}")
    
    # Método 2: BeautifulSoup mejorado
    try:
        print(f"\n   2️⃣ Método BeautifulSoup mejorado:")
        content = extract_article_content_improved(url)
        
        methods_results['improved_bs4'] = {
            'length': len(content),
            'sample': content[:200] if content else '',
            'status': 'success' if len(content) > 100 else 'insufficient'
        }
        
        print(f"      📏 Longitud: {len(content)} caracteres")
        print(f"      📝 Muestra: {content[:100]}..." if content else "      ❌ Sin contenido")
        
    except Exception as e:
        methods_results['improved_bs4'] = {'status': 'error', 'error': str(e)}
        print(f"      ❌ Error: {str(e)}")
    
    # Método 3: Con reintentos
    try:
        print(f"\n   3️⃣ Método con reintentos:")
        content = extract_with_retry(url, max_retries=2)
        
        methods_results['with_retry'] = {
            'length': len(content),
            'sample': content[:200] if content else '',
            'status': 'success' if len(content) > 100 else 'insufficient'
        }
        
        print(f"      📏 Longitud: {len(content)} caracteres")
        print(f"      📝 Muestra: {content[:100]}..." if content else "      ❌ Sin contenido")
        
    except Exception as e:
        methods_results['with_retry'] = {'status': 'error', 'error': str(e)}
        print(f"      ❌ Error: {str(e)}")
    
    return methods_results

def generar_reporte_completo():
    """Genera un reporte completo de efectividad."""
    print("\n" + "="*60)
    print("GENERANDO REPORTE COMPLETO DE EFECTIVIDAD")
    print("="*60)
    
    # Análisis general
    stats = analizar_estadisticas_generales()
    
    # Análisis por feed
    feeds_data = analizar_por_feed()
    
    # Análisis de fallos
    failed_results = analizar_fallos_extraccion(20)
    
    # Resumen de problemas identificados
    print(f"\n🎯 PROBLEMAS IDENTIFICADOS:")
    
    if stats['unprocessed'] > 0:
        print(f"   ⚠️  {stats['unprocessed']} artículos sin procesar")
    
    if stats['processed_failed'] > 0:
        print(f"   ❌ {stats['processed_failed']} artículos con fallos de extracción")
    
    # Analizar resultados de re-extracción
    if failed_results:
        success_count = sum(1 for r in failed_results if r.get('status') == 'success')
        print(f"   🔄 De {len(failed_results)} artículos fallidos probados, {success_count} ahora funcionan")
        
        if success_count > 0:
            print(f"   💡 Esto sugiere que algunos fallos pueden ser temporales (problemas de red, sitio caído, etc.)")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    
    if stats['processed_failed'] > stats['total_articles'] * 0.05:  # Más del 5% de fallos
        print(f"   🔧 Considerar implementar Playwright para sitios problemáticos")
        print(f"   🔧 Revisar y actualizar selectores CSS para sitios específicos")
    
    if stats['unprocessed'] > 0:
        print(f"   ⚡ Ejecutar procesamiento de artículos pendientes")
    
    effectiveness = (stats['total_mentions'] / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
    if effectiveness < 90:
        print(f"   📈 La efectividad actual ({effectiveness:.1f}%) puede mejorarse")
        print(f"   📈 Revisar configuración de palabras clave y feeds")
    
    print(f"\n✅ REPORTE COMPLETADO")
    print(f"   📊 Efectividad actual: {effectiveness:.1f}%")
    print(f"   🎯 Objetivo: 100%")
    print(f"   📈 Margen de mejora: {100 - effectiveness:.1f}%")

if __name__ == "__main__":
    try:
        generar_reporte_completo()
        
        # Opción para probar una URL específica
        print(f"\n" + "="*60)
        test_url = input("\n🔗 ¿Quieres probar una URL específica? (Enter para salir): ").strip()
        if test_url:
            probar_metodos_extraccion(test_url)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Análisis interrumpido por el usuario.")
    except Exception as e:
        print(f"\n\n❌ Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()