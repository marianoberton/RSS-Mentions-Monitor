import logging
from typing import Dict, Any
import feedparser

logger = logging.getLogger(__name__)

# Feeds que contienen el artículo completo en el RSS
FEEDS_CON_CONTENIDO_COMPLETO = {
    # Feeds habilitados
    'infocielo': True,
    'labrujula24': True,
    'lanueva_general': True,
    'lanueva_ciudad': True,
    'lanueva_punta_alta': True,
    'lanueva_region': True,
    'lanueva_pais': True,
    'lanueva_mundo': True,
    'lanueva_seguridad': True,
    'lanueva_deportes': True,
    'lanueva_aplausos': True,
    'lanueva_opinion': True,
    'lanueva_sociedad': True,
    'lpo_ultimasnoticias': True,
    'lpo_politica': True,
    'lpo_economia': True,
    'lpo_ciudad': True,
    'lpo_provincia': True,
    'lpo_conurbano': True,
    'lpo_campo': True,
    'letra_p_judiciales': False,
    'letra_p_ciudad': False,
    'letra_p_politica': False,
    'letra_p_conurbano': False,
    'letra_p_municipios': False,
    'letra_p_sociedad': False,
    'letra_p_economia': False,
    'diario3': False,
    
    # Feeds deshabilitados (según pruebas, todos requieren extracción con BeautifulSoup)
    'clarin': False,
    'lanacion': False,
    'pagina12': False,
    'ambito': False,
    'cronista': False
}

def extraer_contenido_feed(entry: Dict[str, Any], feed_name: str) -> str:
    """Extrae el contenido directamente del feed RSS si está disponible.
    
    Args:
        entry: Entrada del feed RSS parseada por feedparser
        feed_name: Nombre del feed para aplicar reglas específicas si es necesario
        
    Returns:
        str: Contenido extraído del feed o cadena vacía si no se pudo extraer
    """
    contenido = ""
    
    # Verificar si este feed contiene el artículo completo
    if not FEEDS_CON_CONTENIDO_COMPLETO.get(feed_name, False):
        return ""
    
    # Intentar extraer del campo 'content' si existe
    if 'content' in entry:
        if isinstance(entry.content, list) and len(entry.content) > 0:
            contenido = entry.content[0].value
        else:
            contenido = str(entry.content)
    # Si no hay 'content', intentar con 'summary'
    elif 'summary' in entry:
        contenido = entry.summary
    
    # Limpiar el contenido si es necesario (eliminar etiquetas HTML no deseadas, etc.)
    # Aquí se podría implementar una limpieza específica para cada feed si fuera necesario
    
    return contenido

def tiene_contenido_completo(feed_name: str) -> bool:
    """Verifica si un feed contiene el artículo completo en el RSS.
    
    Args:
        feed_name: Nombre del feed a verificar
        
    Returns:
        bool: True si el feed contiene el artículo completo, False en caso contrario
    """
    return FEEDS_CON_CONTENIDO_COMPLETO.get(feed_name, False)