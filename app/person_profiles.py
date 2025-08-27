#!/usr/bin/env python3
"""
Sistema de perfiles de personas políticas.
Genera automáticamente perfiles detallados con estadísticas, tendencias y resúmenes.
"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple
import re
from .storage import get_db_connection, get_person_stats
import logging

logger = logging.getLogger(__name__)

class PersonProfile:
    """Clase para generar y gestionar perfiles de personas políticas."""
    
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_person_profile(self, person_id: int) -> Dict:
        """Obtener perfil completo de una persona."""
        try:
            with self.conn:
                # Información básica de la persona
                cursor = self.conn.execute("""
                    SELECT id, name, full_name, description, position, 
                           political_party, importance_level, created_utc
                    FROM persons WHERE id = ?
                """, (person_id,))
                
                person_data = cursor.fetchone()
                if not person_data:
                    return None
                
                profile = {
                    "id": person_data[0],
                    "name": person_data[1],
                    "full_name": person_data[2],
                    "description": person_data[3],
                    "position": person_data[4],
                    "political_party": person_data[5],
                    "importance_level": person_data[6],
                    "created_at": person_data[7]
                }
                
                # Estadísticas básicas
                stats = get_person_stats(person_id)
                profile["stats"] = stats
                
                # Keywords asociadas
                profile["keywords"] = self._get_person_keywords(person_id)
                
                # Tendencias temporales
                profile["trends"] = self._get_mention_trends(person_id)
                
                # Fuentes más frecuentes
                profile["top_sources"] = self._get_top_sources(person_id)
                
                # Artículos recientes
                profile["recent_articles"] = self._get_recent_articles(person_id, limit=10)
                
                # Análisis de contexto
                profile["context_analysis"] = self._analyze_mention_context(person_id)
                
                # Actividad por día de la semana
                profile["weekly_activity"] = self._get_weekly_activity(person_id)
                
                return profile
                
        except Exception as e:
            logger.error(f"Error obteniendo perfil de persona {person_id}: {e}")
            return None
    
    def _get_person_keywords(self, person_id: int) -> List[Dict]:
        """Obtener keywords asociadas a una persona."""
        cursor = self.conn.execute("""
            SELECT keyword, is_primary, created_utc
            FROM person_keywords 
            WHERE person_id = ?
            ORDER BY is_primary DESC, keyword
        """, (person_id,))
        
        return [{
            "keyword": row[0],
            "is_primary": bool(row[1]),
            "created_at": row[2]
        } for row in cursor.fetchall()]
    
    def _get_mention_trends(self, person_id: int, days: int = 30) -> Dict:
        """Analizar tendencias de menciones en los últimos días."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT DATE(h.detected_utc) as date, COUNT(*) as mentions
            FROM hits h
            WHERE h.person_id = ? AND h.detected_utc >= ?
            GROUP BY DATE(h.detected_utc)
            ORDER BY date
        """, (person_id, start_date.isoformat()))
        
        daily_mentions = {}
        for row in cursor.fetchall():
            daily_mentions[row[0]] = row[1]
        
        # Llenar días sin menciones
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str not in daily_mentions:
                daily_mentions[date_str] = 0
            current_date += timedelta(days=1)
        
        # Calcular tendencia
        mentions_list = list(daily_mentions.values())
        if len(mentions_list) >= 2:
            recent_avg = sum(mentions_list[-7:]) / 7  # Últimos 7 días
            previous_avg = sum(mentions_list[-14:-7]) / 7 if len(mentions_list) >= 14 else recent_avg
            trend = "up" if recent_avg > previous_avg else "down" if recent_avg < previous_avg else "stable"
        else:
            trend = "stable"
        
        return {
            "daily_mentions": daily_mentions,
            "trend": trend,
            "total_period": sum(mentions_list),
            "avg_daily": sum(mentions_list) / len(mentions_list) if mentions_list else 0
        }
    
    def _get_top_sources(self, person_id: int, limit: int = 10) -> List[Dict]:
        """Obtener las fuentes que más mencionan a la persona."""
        cursor = self.conn.execute("""
            SELECT a.site, COUNT(*) as mentions,
                   COUNT(DISTINCT a.id) as articles,
                   MAX(h.detected_utc) as last_mention
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.person_id = ?
            GROUP BY a.site
            ORDER BY mentions DESC
            LIMIT ?
        """, (person_id, limit))
        
        return [{
            "source": row[0],
            "mentions": row[1],
            "articles": row[2],
            "last_mention": row[3]
        } for row in cursor.fetchall()]
    
    def _get_recent_articles(self, person_id: int, limit: int = 10) -> List[Dict]:
        """Obtener artículos recientes que mencionan a la persona."""
        cursor = self.conn.execute("""
            SELECT DISTINCT a.id, a.title, a.link, a.site, a.published_utc,
                   h.where_found, h.detected_utc as mention_time
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            WHERE h.person_id = ?
            ORDER BY h.detected_utc DESC
            LIMIT ?
        """, (person_id, limit))
        
        return [{
            "id": row[0],
            "title": row[1],
            "url": row[2],
            "source": row[3],
            "published_at": row[4],
            "where_found": row[5],
            "mention_time": row[6]
        } for row in cursor.fetchall()]
    
    def _analyze_mention_context(self, person_id: int) -> Dict:
        """Analizar el contexto de las menciones (título vs contenido)."""
        cursor = self.conn.execute("""
            SELECT where_found, COUNT(*) as count
            FROM hits
            WHERE person_id = ?
            GROUP BY where_found
        """, (person_id,))
        
        context_counts = {}
        total = 0
        for row in cursor.fetchall():
            context_counts[row[0]] = row[1]
            total += row[1]
        
        # Calcular porcentajes
        context_percentages = {}
        for context, count in context_counts.items():
            context_percentages[context] = (count / total * 100) if total > 0 else 0
        
        return {
            "counts": context_counts,
            "percentages": context_percentages,
            "total": total
        }
    
    def _get_weekly_activity(self, person_id: int) -> Dict:
        """Analizar actividad por día de la semana."""
        cursor = self.conn.execute("""
            SELECT 
                CASE CAST(strftime('%w', h.detected_utc) AS INTEGER)
                    WHEN 0 THEN 'Domingo'
                    WHEN 1 THEN 'Lunes'
                    WHEN 2 THEN 'Martes'
                    WHEN 3 THEN 'Miércoles'
                    WHEN 4 THEN 'Jueves'
                    WHEN 5 THEN 'Viernes'
                    WHEN 6 THEN 'Sábado'
                END as day_name,
                COUNT(*) as mentions
            FROM hits h
            WHERE h.person_id = ?
            GROUP BY strftime('%w', h.detected_utc)
            ORDER BY CAST(strftime('%w', h.detected_utc) AS INTEGER)
        """, (person_id,))
        
        weekly_activity = {}
        for row in cursor.fetchall():
            weekly_activity[row[0]] = row[1]
        
        # Asegurar que todos los días estén presentes
        days = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        for day in days:
            if day not in weekly_activity:
                weekly_activity[day] = 0
        
        return weekly_activity
    
    def get_all_persons_summary(self) -> List[Dict]:
        """Obtener resumen de todas las personas."""
        cursor = self.conn.execute("""
            SELECT p.id, p.name, p.importance_level,
                   COUNT(h.id) as total_mentions,
                   COUNT(DISTINCT h.article_id) as unique_articles,
                   MAX(h.detected_utc) as last_mention,
                   MIN(h.detected_utc) as first_mention
            FROM persons p
            LEFT JOIN hits h ON p.id = h.person_id
            GROUP BY p.id, p.name, p.importance_level
            ORDER BY p.importance_level DESC, total_mentions DESC
        """)
        
        return [{
            "id": row[0],
            "name": row[1],
            "importance_level": row[2],
            "total_mentions": row[3],
            "unique_articles": row[4],
            "last_mention": row[5],
            "first_mention": row[6]
        } for row in cursor.fetchall()]
    
    def generate_person_report(self, person_id: int) -> str:
        """Generar reporte textual detallado de una persona."""
        profile = self.get_person_profile(person_id)
        if not profile:
            return "Persona no encontrada."
        
        report = []
        report.append(f"=== PERFIL DE {profile['name'].upper()} ===")
        report.append(f"Nombre completo: {profile['full_name']}")
        report.append(f"Cargo: {profile['position']}")
        if profile['political_party']:
            report.append(f"Partido político: {profile['political_party']}")
        report.append(f"Nivel de importancia: {profile['importance_level']}/5")
        report.append(f"Descripción: {profile['description']}")
        report.append("")
        
        # Estadísticas
        stats = profile['stats']
        report.append("=== ESTADÍSTICAS ===")
        report.append(f"Total de menciones: {stats['total_hits']}")
        report.append(f"Artículos únicos: {stats['unique_articles']}")
        report.append(f"Promedio menciones por artículo: {stats['avg_hits_per_article']:.2f}")
        if stats['first_mention']:
            report.append(f"Primera mención: {stats['first_mention']}")
        if stats['last_mention']:
            report.append(f"Última mención: {stats['last_mention']}")
        report.append("")
        
        # Keywords
        report.append("=== KEYWORDS ASOCIADAS ===")
        for kw in profile['keywords']:
            primary = " (PRIMARIA)" if kw['is_primary'] else ""
            report.append(f"- {kw['keyword']}{primary}")
        report.append("")
        
        # Tendencias
        trends = profile['trends']
        report.append("=== TENDENCIAS (ÚLTIMOS 30 DÍAS) ===")
        report.append(f"Total menciones: {trends['total_period']}")
        report.append(f"Promedio diario: {trends['avg_daily']:.1f}")
        report.append(f"Tendencia: {trends['trend'].upper()}")
        report.append("")
        
        # Top fuentes
        report.append("=== PRINCIPALES FUENTES ===")
        for source in profile['top_sources'][:5]:
            report.append(f"- {source['source']}: {source['mentions']} menciones en {source['articles']} artículos")
        report.append("")
        
        # Contexto
        context = profile['context_analysis']
        report.append("=== ANÁLISIS DE CONTEXTO ===")
        for ctx, percentage in context['percentages'].items():
            report.append(f"- {ctx}: {percentage:.1f}% ({context['counts'][ctx]} menciones)")
        report.append("")
        
        # Actividad semanal
        report.append("=== ACTIVIDAD POR DÍA DE LA SEMANA ===")
        weekly = profile['weekly_activity']
        for day in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']:
            report.append(f"- {day}: {weekly.get(day, 0)} menciones")
        
        return "\n".join(report)
    
    def close(self):
        """Cerrar conexión a la base de datos."""
        if self.conn:
            self.conn.close()

# Funciones de conveniencia
def get_person_profile(person_id: int) -> Dict:
    """Obtener perfil de una persona."""
    profiler = PersonProfile()
    try:
        return profiler.get_person_profile(person_id)
    finally:
        profiler.close()

def generate_person_report(person_id: int) -> str:
    """Generar reporte de una persona."""
    profiler = PersonProfile()
    try:
        return profiler.generate_person_report(person_id)
    finally:
        profiler.close()

def get_all_persons_summary() -> List[Dict]:
    """Obtener resumen de todas las personas."""
    profiler = PersonProfile()
    try:
        return profiler.get_all_persons_summary()
    finally:
        profiler.close()