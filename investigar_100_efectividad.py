#!/usr/bin/env python3

from app.storage import get_db_connection
from app.improved_extractor import extract_with_retry
from app.config import config
import time

def analizar_articulos_no_procesados():
    """Analiza los artículos que no han sido procesados para entender por qué."""
    print("🔍 ANÁLISIS DE ARTÍCULOS NO PROCESADOS")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Contar artículos por estado de procesamiento
    cursor = conn.execute("""
        SELECT content_processed, COUNT(*) as count
        FROM articles 
        GROUP BY content_processed
        ORDER BY content_processed
    """)
    
    estados = cursor.fetchall()
    print("📊 ESTADO DE PROCESAMIENTO:")
    for estado, count in estados:
        estado_desc = {
            0: "Sin procesar",
            1: "Procesado exitosamente", 
            2: "Falló extracción",
            3: "Feed deshabilitado"
        }.get(estado, f"Estado {estado}")
        print(f"   {estado}: {estado_desc} - {count} artículos")
    
    # Analizar artículos sin procesar
    cursor = conn.execute("""
        SELECT id, site, title, link, full_content
        FROM articles 
        WHERE content_processed = 0
        LIMIT 5
    """)
    
    unprocessed = cursor.fetchall()
    print(f"\n🔍 ANÁLISIS DE ARTÍCULOS SIN PROCESAR ({len(unprocessed)} ejemplos):")
    
    for i, (article_id, site, title, link, content) in enumerate(unprocessed, 1):
        print(f"\n--- ARTÍCULO {i} ---")
        print(f"ID: {article_id}")
        print(f"Site: {site}")
        print(f"Title: {title[:80]}...")
        print(f"Link: {link}")
        print(f"Content length: {len(content or '')} caracteres")
        
        # Verificar si el feed está habilitado
        cursor = conn.execute("SELECT enabled FROM feeds WHERE site = ?", (site,))
        feed_result = cursor.fetchone()
        feed_enabled = feed_result[0] if feed_result else "No encontrado"
        print(f"Feed habilitado: {feed_enabled}")
        
        # Intentar extraer contenido
        if not content or len(content) < 100:
            print("🔄 Intentando extraer contenido...")
            try:
                start_time = time.time()
                extracted_content = extract_with_retry(link)
                extraction_time = time.time() - start_time
                
                if extracted_content:
                    print(f"   ✅ Extracción exitosa: {len(extracted_content)} caracteres en {extraction_time:.2f}s")
                else:
                    print(f"   ❌ Extracción falló en {extraction_time:.2f}s")
            except Exception as e:
                print(f"   ❌ Error en extracción: {str(e)}")
        else:
            print("   ℹ️ Ya tiene contenido, debería estar procesado")
    
    # Analizar artículos que fallaron en extracción
    cursor = conn.execute("""
        SELECT id, site, title, link
        FROM articles 
        WHERE content_processed = 2
        LIMIT 3
    """)
    
    failed = cursor.fetchall()
    print(f"\n❌ ANÁLISIS DE ARTÍCULOS CON EXTRACCIÓN FALLIDA ({len(failed)} ejemplos):")
    
    for i, (article_id, site, title, link) in enumerate(failed, 1):
        print(f"\n--- ARTÍCULO FALLIDO {i} ---")
        print(f"ID: {article_id}")
        print(f"Site: {site}")
        print(f"Title: {title[:80]}...")
        print(f"Link: {link}")
        
        # Intentar re-extraer con métodos alternativos
        print("🔄 Reintentando extracción con métodos alternativos...")
        try:
            start_time = time.time()
            extracted_content = extract_with_retry(link)
            extraction_time = time.time() - start_time
            
            if extracted_content:
                print(f"   ✅ ¡Extracción exitosa en reintento!: {len(extracted_content)} caracteres en {extraction_time:.2f}s")
                print(f"   💡 Este artículo podría ser reprocesado")
            else:
                print(f"   ❌ Extracción sigue fallando en {extraction_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Error en reintento: {str(e)}")
    
    conn.close()

def calcular_efectividad_maxima_teorica():
    """Calcula cuál sería la efectividad máxima teórica si todos los artículos procesables fueran procesados."""
    print(f"\n📈 CÁLCULO DE EFECTIVIDAD MÁXIMA TEÓRICA")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Total de artículos
    cursor = conn.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    
    # Artículos con menciones actuales
    cursor = conn.execute("SELECT COUNT(*) FROM hits")
    current_mentions = cursor.fetchone()[0]
    
    # Artículos procesados exitosamente
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
    successfully_processed = cursor.fetchone()[0]
    
    # Artículos que fallaron en extracción (no procesables)
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 2")
    extraction_failed = cursor.fetchone()[0]
    
    # Artículos de feeds deshabilitados (no procesables)
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 3")
    disabled_feeds = cursor.fetchone()[0]
    
    # Artículos sin procesar
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    unprocessed = cursor.fetchone()[0]
    
    # Calcular efectividad actual y máxima teórica
    efectividad_actual = (current_mentions / total_articles * 100) if total_articles > 0 else 0
    
    # Asumiendo que los artículos sin procesar podrían tener la misma tasa de menciones
    # que los ya procesados
    tasa_menciones_procesados = (current_mentions / successfully_processed) if successfully_processed > 0 else 0
    menciones_potenciales_adicionales = unprocessed * tasa_menciones_procesados
    
    menciones_maximas_teoricas = current_mentions + menciones_potenciales_adicionales
    efectividad_maxima_teorica = (menciones_maximas_teoricas / total_articles * 100) if total_articles > 0 else 0
    
    print(f"📊 ESTADÍSTICAS ACTUALES:")
    print(f"   📰 Total de artículos: {total_articles}")
    print(f"   ✅ Procesados exitosamente: {successfully_processed}")
    print(f"   ❌ Falló extracción: {extraction_failed}")
    print(f"   🚫 Feeds deshabilitados: {disabled_feeds}")
    print(f"   ⏳ Sin procesar: {unprocessed}")
    print(f"   🎯 Menciones actuales: {current_mentions}")
    
    print(f"\n📈 PROYECCIONES:")
    print(f"   📊 Efectividad actual: {efectividad_actual:.1f}%")
    print(f"   📊 Tasa de menciones en procesados: {tasa_menciones_procesados:.2f} menciones/artículo")
    print(f"   🎯 Menciones potenciales adicionales: {menciones_potenciales_adicionales:.0f}")
    print(f"   📊 Efectividad máxima teórica: {efectividad_maxima_teorica:.1f}%")
    print(f"   📈 Mejora potencial: +{efectividad_maxima_teorica - efectividad_actual:.1f}%")
    
    conn.close()
    
    return {
        'actual': efectividad_actual,
        'maxima_teorica': efectividad_maxima_teorica,
        'mejora_potencial': efectividad_maxima_teorica - efectividad_actual,
        'unprocessed': unprocessed,
        'extraction_failed': extraction_failed
    }

if __name__ == "__main__":
    analizar_articulos_no_procesados()
    resultados = calcular_efectividad_maxima_teorica()
    
    print(f"\n🎯 CONCLUSIONES:")
    if resultados['unprocessed'] > 0:
        print(f"   💡 Hay {resultados['unprocessed']} artículos sin procesar que podrían mejorar la efectividad")
    if resultados['extraction_failed'] > 0:
        print(f"   🔧 Hay {resultados['extraction_failed']} artículos con extracción fallida que podrían ser reintentos")
    if resultados['mejora_potencial'] > 1:
        print(f"   📈 Mejora potencial disponible: +{resultados['mejora_potencial']:.1f}%")
    else:
        print(f"   ✅ El sistema está funcionando cerca de su capacidad máxima")