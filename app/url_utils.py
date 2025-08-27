#!/usr/bin/env python3
"""
Utilidades para canonicalización de URLs y deduplicación de contenido.
"""

import hashlib
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def canonicalize_url(url: str) -> str:
    """
    Canonicaliza una URL removiendo parámetros innecesarios y normalizando el formato.
    
    Args:
        url: URL original
        
    Returns:
        URL canonicalizada
    """
    if not url:
        return url
        
    try:
        parsed = urlparse(url.strip())
        
        # Normalizar el scheme a lowercase
        scheme = parsed.scheme.lower() if parsed.scheme else 'https'
        
        # Normalizar el netloc (domain) a lowercase
        netloc = parsed.netloc.lower() if parsed.netloc else ''
        
        # Remover www. si está presente
        if netloc.startswith('www.'):
            netloc = netloc[4:]
            
        # Normalizar el path
        path = parsed.path
        if not path or path == '/':
            path = '/'
        else:
            # Remover trailing slash excepto para root
            path = path.rstrip('/')
            
        # Filtrar parámetros de query conocidos como tracking/analytics
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', 'dclid', 'twclid',
            '_ga', '_gl', '_gac', 'mc_cid', 'mc_eid',
            'ref', 'referrer', 'source', 'campaign',
            'WT.mc_id', 'WT.mc_ev', 'WT.srch',
            'pk_campaign', 'pk_kwd', 'pk_source',
            'hsCtaTracking', 'hsa_acc', 'hsa_cam', 'hsa_grp', 'hsa_ad', 'hsa_src', 'hsa_tgt', 'hsa_kw', 'hsa_mt', 'hsa_net', 'hsa_ver'
        }
        
        query_params = parse_qs(parsed.query, keep_blank_values=False)
        
        # Filtrar parámetros de tracking
        filtered_params = {
            k: v for k, v in query_params.items() 
            if k.lower() not in tracking_params
        }
        
        # Reconstruir query string ordenado
        query = ''
        if filtered_params:
            # Ordenar parámetros para consistencia
            sorted_params = sorted(filtered_params.items())
            query = urlencode(sorted_params, doseq=True)
            
        # No incluir fragment (#) en URL canónica
        fragment = ''
        
        canonical = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
        
        return canonical
        
    except Exception as e:
        logger.warning(f"Error canonicalizando URL {url}: {e}")
        return url

def calculate_content_hash(title: str, content: Optional[str] = None) -> str:
    """
    Calcula un hash del contenido para detectar duplicados.
    
    Args:
        title: Título del artículo
        content: Contenido completo del artículo (opcional)
        
    Returns:
        Hash SHA-256 del contenido normalizado
    """
    # Normalizar título
    normalized_title = normalize_text(title) if title else ''
    
    # Normalizar contenido si está disponible
    normalized_content = normalize_text(content) if content else ''
    
    # Combinar título y contenido
    combined = f"{normalized_title}|{normalized_content}"
    
    # Calcular hash
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def normalize_text(text: str) -> str:
    """
    Normaliza texto para comparación de contenido.
    
    Args:
        text: Texto original
        
    Returns:
        Texto normalizado
    """
    if not text:
        return ''
        
    # Convertir a lowercase
    normalized = text.lower()
    
    # Remover caracteres especiales y espacios extra
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remover espacios al inicio y final
    normalized = normalized.strip()
    
    return normalized

def is_duplicate_content(title1: str, content1: Optional[str], 
                        title2: str, content2: Optional[str]) -> bool:
    """
    Determina si dos artículos tienen contenido duplicado.
    
    Args:
        title1, content1: Título y contenido del primer artículo
        title2, content2: Título y contenido del segundo artículo
        
    Returns:
        True si el contenido es considerado duplicado
    """
    hash1 = calculate_content_hash(title1, content1)
    hash2 = calculate_content_hash(title2, content2)
    
    return hash1 == hash2

def extract_domain(url: str) -> str:
    """
    Extrae el dominio de una URL.
    
    Args:
        url: URL completa
        
    Returns:
        Dominio extraído
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remover www. si está presente
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception:
        return ''