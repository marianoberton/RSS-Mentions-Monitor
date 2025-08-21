#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y solucionar el problema de duplicados en el dashboard.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from datetime import datetime
import sqlite3

def verificar_esquema_hits():
    """Verifica el esquema de la tabla hits y los índices existentes."""
    print("🔍 VERIFICANDO ESQUEMA DE LA TABLA HITS")
    print("=" * 50)
    
    conn = get_db_connection()
    
    try:
        # Obtener esquema de la tabla hits
        cursor = conn.execute("PRAGMA table_info(hits)")
        columns = cursor.fetchall()
        
        print("📋 COLUMNAS DE LA TABLA HITS:")
        for col in columns:
            print(f"  • {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PK' if col[5] else ''}")
        
        # Verificar índices
        cursor = conn.execute("PRAGMA index_list(hits)")
        indexes = cursor.fetchall()
        
        print(f"\n📊 ÍNDICES EXISTENTES ({len(indexes)}):")
        for idx in indexes:
            print(f"  • {idx[1]} - {'UNIQUE' if idx[2] else 'NO UNIQUE'}")
            
            # Obtener información detallada del índice
            cursor_info = conn.execute(f"PRAGMA index_info({idx[1]})")
            index_info = cursor_info.fetchall()
            columns_in_index = [info[2] for info in index_info]
            print(f"    Columnas: {', '.join(columns_in_index)}")
        
        return len([idx for idx in indexes if idx[2] == 1])  # Contar índices únicos
        
    except Exception as e:
        print(f"❌ Error al verificar esquema: {e}")
        return 0
    finally:
        conn.close()

def buscar_duplicados():
    """Busca hits duplicados en la base de datos."""
    print("\n🔍 BUSCANDO HITS DUPLICADOS")
    print("=" * 50)
    
    conn = get_db_connection()
    
    try:
        # Buscar duplicados por article_id, keyword y where_found
        cursor = conn.execute("""
            SELECT article_id, keyword, where_found, COUNT(*) as count, 
                   GROUP_CONCAT(id) as hit_ids,
                   GROUP_CONCAT(detected_utc) as timestamps
            FROM hits 
            GROUP BY article_id, keyword, where_found
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"⚠️  ENCONTRADOS {len(duplicates)} GRUPOS DE DUPLICADOS:")
            total_duplicate_hits = 0
            
            for i, dup in enumerate(duplicates[:10], 1):  # Mostrar solo los primeros 10
                article_id, keyword, where_found, count, hit_ids, timestamps = dup
                duplicate_count = count - 1  # Restar 1 porque uno debe quedarse
                total_duplicate_hits += duplicate_count
                
                print(f"\n--- DUPLICADO {i} ---")
                print(f"Artículo: {article_id}")
                print(f"Keyword: {keyword}")
                print(f"Ubicación: {where_found}")
                print(f"Cantidad: {count} hits")
                print(f"IDs: {hit_ids}")
                print(f"Timestamps: {timestamps}")
                
                # Obtener información del artículo
                cursor_article = conn.execute("SELECT title, site FROM articles WHERE id = ?", (article_id,))
                article_info = cursor_article.fetchone()
                if article_info:
                    print(f"Título: {article_info[0][:80]}...")
                    print(f"Sitio: {article_info[1]}")
            
            if len(duplicates) > 10:
                print(f"\n... y {len(duplicates) - 10} grupos más")
            
            print(f"\n📊 RESUMEN:")
            print(f"• Total de grupos duplicados: {len(duplicates)}")
            print(f"• Total de hits duplicados a eliminar: {total_duplicate_hits}")
            
            return duplicates
        else:
            print("✅ NO SE ENCONTRARON DUPLICADOS")
            return []
            
    except Exception as e:
        print(f"❌ Error al buscar duplicados: {e}")
        return []
    finally:
        conn.close()

def analizar_estadisticas_dashboard():
    """Analiza las estadísticas que se muestran en el dashboard."""
    print("\n📊 ANALIZANDO ESTADÍSTICAS DEL DASHBOARD")
    print("=" * 50)
    
    conn = get_db_connection()
    
    try:
        # Estadísticas globales
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM articles WHERE content_processed = 1")
        processed_articles = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM hits")
        total_hits = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(DISTINCT article_id) FROM hits")
        articles_with_hits = cursor.fetchone()[0]
        
        print(f"📈 ESTADÍSTICAS GLOBALES:")
        print(f"• Total de artículos: {total_articles}")
        print(f"• Artículos procesados: {processed_articles}")
        print(f"• Total de hits: {total_hits}")
        print(f"• Artículos únicos con hits: {articles_with_hits}")
        print(f"• Promedio de hits por artículo: {total_hits/articles_with_hits:.2f}" if articles_with_hits > 0 else "• Sin artículos con hits")
        
        # Verificar si hay artículos con muchos hits
        cursor = conn.execute("""
            SELECT article_id, COUNT(*) as hit_count
            FROM hits 
            GROUP BY article_id
            HAVING COUNT(*) > 5
            ORDER BY hit_count DESC
            LIMIT 10
        """)
        
        articles_many_hits = cursor.fetchall()
        
        if articles_many_hits:
            print(f"\n⚠️  ARTÍCULOS CON MUCHOS HITS (>5):")
            for article_id, hit_count in articles_many_hits:
                cursor_title = conn.execute("SELECT title, site FROM articles WHERE id = ?", (article_id,))
                article_info = cursor_title.fetchone()
                if article_info:
                    print(f"• {hit_count} hits - {article_info[1]} - {article_info[0][:60]}...")
        
        # Menciones por keyword
        print(f"\n🔍 MENCIONES POR KEYWORD:")
        cursor = conn.execute("""
            SELECT keyword, COUNT(*) as count
            FROM hits
            GROUP BY keyword
            ORDER BY count DESC
        """)
        
        keyword_stats = cursor.fetchall()
        for keyword, count in keyword_stats:
            print(f"• {keyword}: {count} menciones")
            
    except Exception as e:
        print(f"❌ Error al analizar estadísticas: {e}")
    finally:
        conn.close()

def crear_indice_unico():
    """Crea un índice único para prevenir duplicados futuros."""
    print("\n🛡️ CREANDO ÍNDICE ÚNICO PARA PREVENIR DUPLICADOS")
    print("=" * 50)
    
    conn = get_db_connection()
    
    try:
        # Intentar crear el índice único
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hits_unique 
            ON hits(article_id, keyword, where_found)
        """)
        
        print("✅ Índice único creado exitosamente")
        print("   Nombre: idx_hits_unique")
        print("   Columnas: article_id, keyword, where_found")
        
        return True
        
    except sqlite3.IntegrityError as e:
        print(f"⚠️  No se pudo crear el índice único debido a duplicados existentes: {e}")
        print("   Primero elimina los duplicados y luego crea el índice")
        return False
    except Exception as e:
        print(f"❌ Error al crear índice único: {e}")
        return False
    finally:
        conn.close()

def eliminar_duplicados(duplicates):
    """Elimina los hits duplicados manteniendo solo el más antiguo."""
    if not duplicates:
        print("\n✅ No hay duplicados para eliminar")
        return 0
    
    print(f"\n🗑️ ELIMINANDO {len(duplicates)} GRUPOS DE DUPLICADOS")
    print("=" * 50)
    
    conn = get_db_connection()
    total_deleted = 0
    
    try:
        with conn:
            for dup in duplicates:
                hit_ids = dup[4].split(',')  # IDs de los hits duplicados
                
                if len(hit_ids) > 1:
                    # Mantener el primer hit (más antiguo) y eliminar los demás
                    hits_to_delete = hit_ids[1:]
                    
                    for hit_id in hits_to_delete:
                        cursor = conn.execute("DELETE FROM hits WHERE id = ?", (int(hit_id),))
                        total_deleted += 1
                        print(f"  ✅ Eliminado hit duplicado ID: {hit_id}")
        
        print(f"\n📊 RESUMEN DE ELIMINACIÓN:")
        print(f"• Total de hits duplicados eliminados: {total_deleted}")
        print(f"• Grupos de duplicados procesados: {len(duplicates)}")
        
        return total_deleted
        
    except Exception as e:
        print(f"❌ Error al eliminar duplicados: {e}")
        return 0
    finally:
        conn.close()

def main():
    """Función principal."""
    print("🔧 VERIFICACIÓN Y SOLUCIÓN DE DUPLICADOS EN DASHBOARD")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Verificar esquema
    unique_indexes = verificar_esquema_hits()
    
    # 2. Analizar estadísticas
    analizar_estadisticas_dashboard()
    
    # 3. Buscar duplicados
    duplicates = buscar_duplicados()
    
    # 4. Si hay duplicados, ofrecer eliminarlos
    if duplicates:
        print(f"\n⚠️  SE ENCONTRARON {len(duplicates)} GRUPOS DE DUPLICADOS")
        print("\n🔧 SOLUCIONES DISPONIBLES:")
        print("1. Eliminar duplicados existentes")
        print("2. Crear índice único para prevenir futuros duplicados")
        print("3. Ambas acciones")
        
        # Para automatizar, ejecutar ambas acciones
        print("\n🚀 EJECUTANDO SOLUCIÓN AUTOMÁTICA...")
        
        # Eliminar duplicados
        deleted_count = eliminar_duplicados(duplicates)
        
        # Crear índice único
        if deleted_count > 0:
            index_created = crear_indice_unico()
            if index_created:
                print("\n✅ SOLUCIÓN COMPLETADA:")
                print(f"• {deleted_count} hits duplicados eliminados")
                print("• Índice único creado para prevenir futuros duplicados")
                print("• El dashboard ahora mostrará estadísticas correctas")
            else:
                print("\n⚠️  Duplicados eliminados pero no se pudo crear el índice único")
        
    else:
        # No hay duplicados, solo verificar/crear índice único
        if unique_indexes == 0:
            print("\n🛡️ No hay duplicados, pero creando índice único como prevención...")
            crear_indice_unico()
        else:
            print("\n✅ SISTEMA EN PERFECTO ESTADO:")
            print("• No hay duplicados")
            print("• Índice único ya existe")
            print("• Dashboard mostrando estadísticas correctas")
    
    print("\n🎯 RECOMENDACIONES POST-SOLUCIÓN:")
    print("• Reinicia el servidor web para ver los cambios")
    print("• Verifica que las estadísticas del dashboard sean correctas")
    print("• Monitorea que no se generen nuevos duplicados")
    
    print("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    main()