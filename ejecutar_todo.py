#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejecutar Todo - Procesamiento completo de feeds y búsqueda de menciones

Este script ejecuta un procesamiento completo del sistema:
1. Procesa todos los feeds RSS disponibles
2. Guarda nuevos artículos encontrados
3. Busca menciones de todos los candidatos activos
4. Genera estadísticas detalladas del procesamiento
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.storage import get_db_connection
from app.tasks import process_feed
from app.mention_detector import find_mentions_in_article

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EjecutarTodoProcessor:
    def __init__(self):
        self.stats = {
            'inicio': datetime.now(),
            'feeds_procesados': 0,
            'feeds_exitosos': 0,
            'feeds_con_error': 0,
            'articulos_nuevos': 0,
            'articulos_duplicados': 0,
            'menciones_encontradas': 0,
            'candidatos_mencionados': set(),
            'errores': [],
            'feeds_detalles': []
        }
    
    def obtener_feeds_activos(self) -> List[Dict]:
        """Obtiene todos los feeds RSS activos de la base de datos."""
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.execute("""
                    SELECT id, name, url, is_enabled, last_success_utc
                    FROM feed_state 
                    WHERE is_enabled = 1
                    ORDER BY name
                """)
                feeds = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Encontrados {len(feeds)} feeds activos")
            return feeds
        except Exception as e:
            error_msg = f"Error al obtener feeds: {e}"
            logger.error(error_msg)
            self.stats['errores'].append(error_msg)
            return []
    
    def obtener_candidatos_activos(self) -> List[Dict]:
        """Obtiene todos los candidatos activos con sus keywords."""
        try:
            conn = get_db_connection()
            with conn:
                cursor = conn.execute("""
                    SELECT DISTINCT c.id, c.name, c.full_name
                    FROM candidates c
                    INNER JOIN candidate_keywords ck ON c.id = ck.candidate_id
                    WHERE c.is_active = 1 AND ck.is_active = 1
                    ORDER BY c.name
                """)
                candidatos = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Encontrados {len(candidatos)} candidatos activos")
            return candidatos
        except Exception as e:
            error_msg = f"Error al obtener candidatos: {e}"
            logger.error(error_msg)
            self.stats['errores'].append(error_msg)
            return []
    
    def procesar_feed(self, feed: Dict) -> Dict:
        """Procesa un feed individual y retorna estadísticas."""
        feed_stats = {
            'nombre': feed['name'],
            'url': feed['url'],
            'exitoso': False,
            'articulos_nuevos': 0,
            'articulos_duplicados': 0,
            'menciones': 0,
            'error': None,
            'tiempo_procesamiento': None
        }
        
        inicio_feed = datetime.now()
        
        try:
            logger.info(f"Procesando feed: {feed['name']}")
            
            # Contar artículos antes del procesamiento
            conn = get_db_connection()
            with conn:
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                articulos_antes = cursor.fetchone()[0]
            
            # Obtener keywords activas
            from app.storage import get_all_active_keywords
            keywords = get_all_active_keywords()
            
            # Procesar el feed
            process_feed(feed, keywords)
            
            # Contar artículos después del procesamiento
            with conn:
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                articulos_despues = cursor.fetchone()[0]
            
            feed_stats['articulos_nuevos'] = articulos_despues - articulos_antes
            feed_stats['exitoso'] = True
            
            self.stats['feeds_exitosos'] += 1
            self.stats['articulos_nuevos'] += feed_stats['articulos_nuevos']
            
            logger.info(f"Feed {feed['name']} procesado: {feed_stats['articulos_nuevos']} artículos nuevos")
            
        except Exception as e:
            error_msg = f"Error procesando feed {feed['name']}: {e}"
            logger.error(error_msg)
            feed_stats['error'] = str(e)
            self.stats['feeds_con_error'] += 1
            self.stats['errores'].append(error_msg)
        
        feed_stats['tiempo_procesamiento'] = (datetime.now() - inicio_feed).total_seconds()
        return feed_stats
    
    def buscar_menciones_articulos_recientes(self, horas_atras: int = 24) -> int:
        """Busca menciones en artículos procesados recientemente."""
        try:
            conn = get_db_connection()
            fecha_limite = datetime.now() - timedelta(hours=horas_atras)
            
            # Obtener artículos recientes
            with conn:
                cursor = conn.execute("""
                    SELECT id, title, full_content, link, published_utc
                    FROM articles 
                    WHERE inserted_utc >= ?
                    ORDER BY inserted_utc DESC
                """, (fecha_limite,))
                articulos = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Buscando menciones en {len(articulos)} artículos recientes")
            
            menciones_totales = 0
            
            for articulo in articulos:
                try:
                    # Buscar menciones en este artículo
                    menciones = find_mentions_in_article(
                        articulo['id'],
                        articulo['title'],
                        articulo['full_content'] or '',
                        articulo['link']
                    )
                    
                    if menciones:
                        menciones_totales += len(menciones)
                        # Agregar candidatos mencionados a las estadísticas
                        for mencion in menciones:
                            self.stats['candidatos_mencionados'].add(mencion.get('candidate_name', 'Desconocido'))
                
                except Exception as e:
                    error_msg = f"Error buscando menciones en artículo {articulo['id']}: {e}"
                    logger.warning(error_msg)
                    continue
            
            self.stats['menciones_encontradas'] = menciones_totales
            logger.info(f"Encontradas {menciones_totales} menciones en total")
            
            return menciones_totales
            
        except Exception as e:
            error_msg = f"Error en búsqueda de menciones: {e}"
            logger.error(error_msg)
            self.stats['errores'].append(error_msg)
            return 0
    
    def ejecutar_procesamiento_completo(self) -> Dict:
        """Ejecuta el procesamiento completo y retorna estadísticas."""
        logger.info("=== INICIANDO PROCESAMIENTO COMPLETO ===")
        
        # 1. Obtener feeds activos
        feeds = self.obtener_feeds_activos()
        if not feeds:
            logger.error("No se encontraron feeds activos")
            return self.generar_reporte_final()
        
        # 2. Obtener candidatos activos
        candidatos = self.obtener_candidatos_activos()
        if not candidatos:
            logger.warning("No se encontraron candidatos activos")
        
        # 3. Procesar cada feed
        logger.info(f"Procesando {len(feeds)} feeds...")
        for feed in feeds:
            feed_stats = self.procesar_feed(feed)
            self.stats['feeds_detalles'].append(feed_stats)
            self.stats['feeds_procesados'] += 1
        
        # 4. Buscar menciones en artículos recientes
        logger.info("Buscando menciones en artículos recientes...")
        self.buscar_menciones_articulos_recientes()
        
        # 5. Generar reporte final
        return self.generar_reporte_final()
    
    def generar_reporte_final(self) -> Dict:
        """Genera el reporte final con todas las estadísticas."""
        fin = datetime.now()
        duracion = fin - self.stats['inicio']
        
        reporte = {
            'resumen': {
                'inicio': self.stats['inicio'].strftime('%Y-%m-%d %H:%M:%S'),
                'fin': fin.strftime('%Y-%m-%d %H:%M:%S'),
                'duracion_segundos': duracion.total_seconds(),
                'duracion_legible': str(duracion).split('.')[0]
            },
            'feeds': {
                'total_procesados': self.stats['feeds_procesados'],
                'exitosos': self.stats['feeds_exitosos'],
                'con_errores': self.stats['feeds_con_error'],
                'tasa_exito': f"{(self.stats['feeds_exitosos'] / max(1, self.stats['feeds_procesados']) * 100):.1f}%"
            },
            'articulos': {
                'nuevos_encontrados': self.stats['articulos_nuevos'],
                'duplicados_omitidos': self.stats['articulos_duplicados']
            },
            'menciones': {
                'total_encontradas': self.stats['menciones_encontradas'],
                'candidatos_mencionados': len(self.stats['candidatos_mencionados']),
                'lista_candidatos': sorted(list(self.stats['candidatos_mencionados']))
            },
            'errores': {
                'total': len(self.stats['errores']),
                'lista': self.stats['errores']
            },
            'detalles_feeds': self.stats['feeds_detalles']
        }
        
        return reporte

def main():
    """Función principal del script."""
    try:
        processor = EjecutarTodoProcessor()
        reporte = processor.ejecutar_procesamiento_completo()
        
        # Imprimir reporte en formato legible
        print("\n" + "="*60)
        print("           REPORTE DE PROCESAMIENTO COMPLETO")
        print("="*60)
        
        print(f"\n📅 TIEMPO:")
        print(f"   Inicio: {reporte['resumen']['inicio']}")
        print(f"   Fin: {reporte['resumen']['fin']}")
        print(f"   Duración: {reporte['resumen']['duracion_legible']}")
        
        print(f"\n📡 FEEDS PROCESADOS:")
        print(f"   Total: {reporte['feeds']['total_procesados']}")
        print(f"   Exitosos: {reporte['feeds']['exitosos']}")
        print(f"   Con errores: {reporte['feeds']['con_errores']}")
        print(f"   Tasa de éxito: {reporte['feeds']['tasa_exito']}")
        
        print(f"\n📰 ARTÍCULOS:")
        print(f"   Nuevos encontrados: {reporte['articulos']['nuevos_encontrados']}")
        print(f"   Duplicados omitidos: {reporte['articulos']['duplicados_omitidos']}")
        
        print(f"\n🎯 MENCIONES:")
        print(f"   Total encontradas: {reporte['menciones']['total_encontradas']}")
        print(f"   Candidatos mencionados: {reporte['menciones']['candidatos_mencionados']}")
        if reporte['menciones']['lista_candidatos']:
            print(f"   Lista: {', '.join(reporte['menciones']['lista_candidatos'])}")
        
        if reporte['errores']['total'] > 0:
            print(f"\n❌ ERRORES ({reporte['errores']['total']}):")
            for i, error in enumerate(reporte['errores']['lista'][:5], 1):
                print(f"   {i}. {error}")
            if len(reporte['errores']['lista']) > 5:
                print(f"   ... y {len(reporte['errores']['lista']) - 5} errores más")
        
        print(f"\n📊 DETALLES POR FEED:")
        for feed in reporte['detalles_feeds']:
            status = "✅" if feed['exitoso'] else "❌"
            print(f"   {status} {feed['nombre']}: {feed['articulos_nuevos']} artículos nuevos")
            if feed['error']:
                print(f"      Error: {feed['error']}")
        
        print("\n" + "="*60)
        print("                    PROCESAMIENTO COMPLETADO")
        print("="*60)
        
        # Retornar código de salida basado en el éxito
        if reporte['feeds']['con_errores'] == 0:
            return 0
        elif reporte['feeds']['exitosos'] > 0:
            return 1  # Éxito parcial
        else:
            return 2  # Fallo completo
            
    except Exception as e:
        logger.error(f"Error crítico en procesamiento: {e}")
        print(f"\n❌ ERROR CRÍTICO: {e}")
        return 3

if __name__ == '__main__':
    sys.exit(main())