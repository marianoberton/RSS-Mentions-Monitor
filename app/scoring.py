#!/usr/bin/env python3
"""
Sistema de scoring para menciones basado en múltiples factores:
- Ubicación de la mención (título > cuerpo)
- Tipo de keyword (alias vs nombre principal)
- Credibilidad del feed
- Freshness (qué tan reciente es el artículo)
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Configuración de scoring
SCORING_CONFIG = {
    # Pesos por ubicación de la mención
    'location_weights': {
        'title': 3.0,
        'content': 1.0,
        'description': 2.0,
        'summary': 1.5
    },
    
    # Pesos por tipo de keyword
    'keyword_weights': {
        'primary': 1.0,      # Nombre principal
        'alias': 0.8,        # Alias o variación
        'secondary': 0.6     # Keywords secundarias
    },
    
    # Credibilidad por dominio (se puede expandir)
    'feed_credibility': {
        'infocielo.com': 0.9,
        'lanueva.com': 0.85,
        'lapoliticaonline.com': 0.8,
        'letrap.com.ar': 0.75,
        'diario3.com.ar': 0.7,
        'default': 0.6
    },
    
    # Parámetros de freshness
    'freshness': {
        'max_hours': 48,      # Después de 48 horas, el score de freshness es mínimo
        'decay_factor': 0.5   # Factor de decaimiento exponencial
    }
}

def calculate_mention_score(article: Dict[str, Any], hit: Dict[str, Any], 
                           person_keywords: Dict[str, str]) -> float:
    """
    Calcula el score de una mención basado en múltiples factores.
    
    Args:
        article: Diccionario con datos del artículo
        hit: Diccionario con datos del hit
        person_keywords: Mapeo de keyword -> tipo (primary, alias, secondary)
        
    Returns:
        Score calculado (0.0 - 10.0)
    """
    try:
        # Factor 1: Ubicación de la mención
        location_score = get_location_score(hit.get('where_found', 'content'))
        
        # Factor 2: Tipo de keyword
        keyword_score = get_keyword_score(hit.get('keyword', ''), person_keywords)
        
        # Factor 3: Credibilidad del feed
        credibility_score = get_credibility_score(article.get('site', ''))
        
        # Factor 4: Freshness
        freshness_score = get_freshness_score(article.get('published_utc', ''))
        
        # Calcular score final (promedio ponderado)
        base_score = (
            location_score * 0.4 +      # 40% peso a la ubicación
            keyword_score * 0.25 +      # 25% peso al tipo de keyword
            credibility_score * 0.2 +   # 20% peso a la credibilidad
            freshness_score * 0.15      # 15% peso a la frescura
        )
        
        # Normalizar a escala 0-10
        final_score = min(10.0, max(0.0, base_score * 10))
        
        logger.debug(f"Score calculado: {final_score:.2f} (loc:{location_score:.2f}, kw:{keyword_score:.2f}, cred:{credibility_score:.2f}, fresh:{freshness_score:.2f})")
        
        return round(final_score, 2)
        
    except Exception as e:
        logger.error(f"Error calculando score: {e}")
        return 1.0  # Score por defecto

def get_location_score(where_found: str) -> float:
    """
    Calcula el score basado en dónde se encontró la mención.
    
    Args:
        where_found: Ubicación de la mención (title, content, etc.)
        
    Returns:
        Score normalizado (0.0 - 1.0)
    """
    weights = SCORING_CONFIG['location_weights']
    weight = weights.get(where_found.lower(), weights['content'])
    
    # Normalizar al peso máximo
    max_weight = max(weights.values())
    return weight / max_weight

def get_keyword_score(keyword: str, person_keywords: Dict[str, str]) -> float:
    """
    Calcula el score basado en el tipo de keyword.
    
    Args:
        keyword: Keyword que generó el hit
        person_keywords: Mapeo de keyword -> tipo
        
    Returns:
        Score normalizado (0.0 - 1.0)
    """
    weights = SCORING_CONFIG['keyword_weights']
    keyword_type = person_keywords.get(keyword, 'secondary')
    weight = weights.get(keyword_type, weights['secondary'])
    
    # Normalizar al peso máximo
    max_weight = max(weights.values())
    return weight / max_weight

def get_credibility_score(site: str) -> float:
    """
    Calcula el score basado en la credibilidad del feed.
    
    Args:
        site: Nombre del sitio/feed
        
    Returns:
        Score normalizado (0.0 - 1.0)
    """
    credibility = SCORING_CONFIG['feed_credibility']
    
    # Buscar por dominio exacto o usar default
    site_lower = site.lower()
    for domain, score in credibility.items():
        if domain != 'default' and domain in site_lower:
            return score
    
    return credibility['default']

def get_freshness_score(published_utc: str) -> float:
    """
    Calcula el score basado en qué tan reciente es el artículo.
    
    Args:
        published_utc: Timestamp de publicación en formato ISO
        
    Returns:
        Score normalizado (0.0 - 1.0)
    """
    if not published_utc:
        return 0.5  # Score neutral si no hay fecha
    
    try:
        # Parsear fecha de publicación
        if published_utc.endswith('Z'):
            published_utc = published_utc[:-1] + '+00:00'
        
        published_dt = datetime.fromisoformat(published_utc.replace('Z', '+00:00'))
        now = datetime.now(published_dt.tzinfo)
        
        # Calcular diferencia en horas
        hours_diff = (now - published_dt).total_seconds() / 3600
        
        if hours_diff < 0:
            return 1.0  # Artículo futuro (error de fecha), score máximo
        
        max_hours = SCORING_CONFIG['freshness']['max_hours']
        decay_factor = SCORING_CONFIG['freshness']['decay_factor']
        
        if hours_diff >= max_hours:
            return 0.1  # Score mínimo para artículos muy antiguos
        
        # Decaimiento exponencial
        freshness = math.exp(-decay_factor * hours_diff / max_hours)
        
        return max(0.1, freshness)
        
    except Exception as e:
        logger.warning(f"Error parseando fecha {published_utc}: {e}")
        return 0.5  # Score neutral en caso de error

def get_person_keywords_map(person_id: int) -> Dict[str, str]:
    """
    Obtiene el mapeo de keywords para una persona específica.
    
    Args:
        person_id: ID de la persona
        
    Returns:
        Diccionario keyword -> tipo
    """
    from app.storage import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT keyword, is_primary 
            FROM person_keywords 
            WHERE person_id = ? AND is_active = 1
        """, (person_id,))
        
        keywords_map = {}
        for keyword, is_primary in cursor.fetchall():
            if is_primary:
                keywords_map[keyword] = 'primary'
            else:
                keywords_map[keyword] = 'alias'
        
        return keywords_map
        
    except Exception as e:
        logger.error(f"Error obteniendo keywords para persona {person_id}: {e}")
        return {}
    finally:
        conn.close()

def update_hit_score(hit_id: int, score: float):
    """
    Actualiza el score de un hit específico.
    
    Args:
        hit_id: ID del hit
        score: Nuevo score
    """
    from app.storage import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE hits 
            SET score = ?
            WHERE id = ?
        """, (score, hit_id))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error actualizando score del hit {hit_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def calculate_and_update_scores_for_article(article_id: int):
    """
    Calcula y actualiza los scores para todos los hits de un artículo.
    
    Args:
        article_id: ID del artículo
    """
    from app.storage import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Obtener artículo y sus hits
        cursor.execute("""
            SELECT a.id, a.site, a.title, a.published_utc,
                   h.id as hit_id, h.person_id, h.keyword, h.where_found
            FROM articles a
            JOIN hits h ON a.id = h.article_id
            WHERE a.id = ?
        """, (article_id,))
        
        rows = cursor.fetchall()
        
        if not rows:
            return
        
        # Procesar cada hit
        for row in rows:
            article = {
                'id': row[0],
                'site': row[1],
                'title': row[2],
                'published_utc': row[3]
            }
            
            hit = {
                'id': row[4],
                'person_id': row[5],
                'keyword': row[6],
                'where_found': row[7]
            }
            
            # Obtener keywords de la persona
            person_keywords = get_person_keywords_map(hit['person_id'])
            
            # Calcular score
            score = calculate_mention_score(article, hit, person_keywords)
            
            # Actualizar score
            update_hit_score(hit['id'], score)
            
            logger.debug(f"Score actualizado para hit {hit['id']}: {score}")
        
    except Exception as e:
        logger.error(f"Error calculando scores para artículo {article_id}: {e}")
    finally:
        conn.close()

def get_top_mentions(limit: int = 10, min_score: float = 5.0) -> list:
    """
    Obtiene las menciones con mayor score.
    
    Args:
        limit: Número máximo de menciones a retornar
        min_score: Score mínimo requerido
        
    Returns:
        Lista de menciones ordenadas por score
    """
    from app.storage import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT h.id, h.score, h.keyword, h.where_found, h.detected_utc,
                   a.title, a.site, a.link, a.published_utc,
                   p.name, p.full_name
            FROM hits h
            JOIN articles a ON h.article_id = a.id
            JOIN persons p ON h.person_id = p.id
            WHERE h.score >= ?
            ORDER BY h.score DESC, h.detected_utc DESC
            LIMIT ?
        """, (min_score, limit))
        
        return cursor.fetchall()
        
    except Exception as e:
        logger.error(f"Error obteniendo top menciones: {e}")
        return []
    finally:
        conn.close()