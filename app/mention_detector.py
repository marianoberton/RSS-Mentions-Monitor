#!/usr/bin/env python3
"""
Módulo para detectar menciones de candidatos en artículos.
"""

import logging
from typing import List, Dict, Any
from .storage import get_db_connection
from .matcher import find_keyword
from .config import config
from .utils import get_utc_now

logger = logging.getLogger(__name__)

def find_mentions_in_article(article_id: int, title: str, content: str, url: str) -> List[Dict[str, Any]]:
    """
    Busca menciones de palabras clave en un artículo.
    
    Args:
        article_id: ID del artículo
        title: Título del artículo
        content: Contenido completo del artículo
        url: URL del artículo
    
    Returns:
        Lista de menciones encontradas
    """
    menciones = []
    keywords = config.get("keywords", [])
    
    if not keywords:
        logger.warning("No hay palabras clave configuradas")
        return menciones
    
    conn = get_db_connection()
    now_utc = get_utc_now()
    
    try:
        for keyword in keywords:
            # Buscar en título primero
            if find_keyword(title, [keyword]):
                # Verificar si ya existe esta mención
                cursor = conn.execute(
                    "SELECT id FROM hits WHERE article_id = ? AND keyword = ?",
                    (article_id, keyword)
                )
                if not cursor.fetchone():
                    # Guardar la mención
                    conn.execute(
                        "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                        (article_id, keyword, "title", now_utc.isoformat())
                    )
                    menciones.append({
                        'keyword': keyword,
                        'where_found': 'title',
                        'article_id': article_id,
                        'url': url
                    })
                    logger.info(f"Mención encontrada en título: {keyword} - {title[:50]}...")
            
            # Buscar en contenido si no se encontró en título
            elif content and find_keyword(content, [keyword]):
                # Verificar si ya existe esta mención
                cursor = conn.execute(
                    "SELECT id FROM hits WHERE article_id = ? AND keyword = ?",
                    (article_id, keyword)
                )
                if not cursor.fetchone():
                    # Guardar la mención
                    conn.execute(
                        "INSERT INTO hits (article_id, keyword, where_found, detected_utc) VALUES (?, ?, ?, ?)",
                        (article_id, keyword, "content", now_utc.isoformat())
                    )
                    menciones.append({
                        'keyword': keyword,
                        'where_found': 'content',
                        'article_id': article_id,
                        'url': url
                    })
                    logger.info(f"Mención encontrada en contenido: {keyword} - {title[:50]}...")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error al buscar menciones en artículo {article_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return menciones