import logging
import sys
from app.config import config
from app.storage import get_db_connection, init_db, get_unprocessed_articles
from app.tasks import extract_article_content, find_keyword

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_content_extraction():
    """Prueba la extracción de contenido de artículos y la búsqueda de palabras clave."""
    # Obtener artículos no procesados
    unprocessed_articles = get_unprocessed_articles(limit=5)
    
    if not unprocessed_articles:
        logger.info("No hay artículos sin procesar. Ejecuta main.py primero para obtener artículos.")
        return
    
    logger.info(f"Se encontraron {len(unprocessed_articles)} artículos sin procesar.")
    
    # Palabras clave a buscar
    keywords = config["keywords"]
    logger.info(f"Palabras clave configuradas: {keywords}")
    
    # Procesar cada artículo
    for article in unprocessed_articles:
        article_id = article["id"]
        url = article["link"]
        
        logger.info(f"Procesando artículo {article_id} de URL: {url}")
        
        # Extraer contenido
        content = extract_article_content(url)
        
        if not content:
            logger.warning(f"No se pudo extraer contenido del artículo {article_id}")
            continue
        
        # Mostrar una parte del contenido extraído
        preview = content[:200] + "..." if len(content) > 200 else content
        logger.info(f"Contenido extraído (primeros 200 caracteres): {preview}")
        
        # Buscar palabras clave en el contenido
        for keyword in keywords:
            if find_keyword(content, [keyword]):
                logger.info(f"¡Palabra clave '{keyword}' encontrada en el contenido!")
            else:
                logger.info(f"Palabra clave '{keyword}' NO encontrada en el contenido.")

def main():
    logger.info("Iniciando prueba de extracción de contenido...")
    
    # Verificar que la base de datos esté inicializada
    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        logger.info(f"Base de datos conectada. Hay {article_count} artículos en total.")
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")
        logger.info("Inicializando base de datos...")
        init_db()
    
    # Ejecutar la prueba
    test_content_extraction()
    
    logger.info("Prueba de extracción de contenido finalizada.")

if __name__ == "__main__":
    main()