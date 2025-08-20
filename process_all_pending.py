#!/usr/bin/env python3

from app.tasks import process_article_content
from app.storage import get_db_connection
import time

def get_unprocessed_count():
    """Obtiene el número de artículos sin procesar."""
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def process_all_pending_articles():
    """Procesa todos los artículos pendientes ejecutando process_article_content múltiples veces."""
    print("🚀 PROCESAMIENTO COMPLETO DE ARTÍCULOS PENDIENTES")
    print("=" * 60)
    
    initial_count = get_unprocessed_count()
    print(f"📊 Artículos sin procesar inicialmente: {initial_count}")
    
    if initial_count == 0:
        print("✅ No hay artículos pendientes para procesar.")
        return
    
    iteration = 0
    total_processed = 0
    start_time = time.time()
    
    while True:
        iteration += 1
        current_count = get_unprocessed_count()
        
        if current_count == 0:
            print(f"\n✅ ¡Todos los artículos han sido procesados!")
            break
            
        print(f"\n🔄 Iteración {iteration} - Artículos restantes: {current_count}")
        
        try:
            # Ejecutar el procesamiento (procesa hasta 10 artículos)
            iteration_start = time.time()
            process_article_content()
            iteration_time = time.time() - iteration_start
            
            # Verificar cuántos se procesaron en esta iteración
            new_count = get_unprocessed_count()
            processed_this_iteration = current_count - new_count
            total_processed += processed_this_iteration
            
            print(f"   ✅ Procesados en esta iteración: {processed_this_iteration}")
            print(f"   ⏱️ Tiempo de iteración: {iteration_time:.2f}s")
            print(f"   📈 Total procesados: {total_processed}")
            
            # Si no se procesó ningún artículo, algo está mal
            if processed_this_iteration == 0:
                print(f"   ⚠️ No se procesaron artículos en esta iteración. Verificando...")
                
                # Verificar si hay artículos de feeds deshabilitados
                conn = get_db_connection()
                cursor = conn.execute("""
                    SELECT site, COUNT(*) as count 
                    FROM articles 
                    WHERE content_processed = 0 
                    GROUP BY site
                """)
                unprocessed_by_site = cursor.fetchall()
                conn.close()
                
                if unprocessed_by_site:
                    print(f"   📋 Artículos sin procesar por sitio:")
                    for site, count in unprocessed_by_site:
                        print(f"      - {site}: {count} artículos")
                
                # Esperar un poco antes de la siguiente iteración
                time.sleep(2)
            
            # Pequeña pausa entre iteraciones para no sobrecargar
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error en iteración {iteration}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    total_time = time.time() - start_time
    final_count = get_unprocessed_count()
    
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   🎯 Artículos iniciales: {initial_count}")
    print(f"   ✅ Artículos procesados: {total_processed}")
    print(f"   📋 Artículos restantes: {final_count}")
    print(f"   🔄 Iteraciones ejecutadas: {iteration}")
    print(f"   ⏱️ Tiempo total: {total_time:.2f}s")
    print(f"   📈 Efectividad: {(total_processed/initial_count*100):.1f}%" if initial_count > 0 else "   📈 Efectividad: N/A")
    
    if final_count > 0:
        print(f"\n⚠️ Quedan {final_count} artículos sin procesar.")
        print(f"   💡 Esto puede deberse a:")
        print(f"      - Feeds deshabilitados")
        print(f"      - Errores de extracción")
        print(f"      - Problemas de conectividad")
    else:
        print(f"\n🎉 ¡Procesamiento completado exitosamente!")

if __name__ == "__main__":
    process_all_pending_articles()