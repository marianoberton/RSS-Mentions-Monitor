import feedparser
import json
import sys

# Lista de feeds habilitados
feeds = [
    {"name": "infocielo", "url": "https://www.infocielo.com/feed"},
    {"name": "labrujula24", "url": "https://www.labrujula24.com/feed/"},
    {"name": "lanueva_general", "url": "http://www.lanueva.com/news/rss/index"},
    {"name": "lanueva_ciudad", "url": "http://www.lanueva.com/news/rss/category/1"},
    {"name": "lanueva_punta_alta", "url": "http://www.lanueva.com/news/rss/category/2"},
    {"name": "lanueva_region", "url": "http://www.lanueva.com/news/rss/category/3"},
    {"name": "lanueva_pais", "url": "http://www.lanueva.com/news/rss/category/4"},
    {"name": "lanueva_mundo", "url": "http://www.lanueva.com/news/rss/category/5"},
    {"name": "lanueva_seguridad", "url": "http://www.lanueva.com/news/rss/category/6"},
    {"name": "lanueva_deportes", "url": "http://www.lanueva.com/news/rss/category/7"},
    {"name": "lanueva_aplausos", "url": "http://www.lanueva.com/news/rss/category/8"},
    {"name": "lanueva_opinion", "url": "http://www.lanueva.com/news/rss/category/9"},
    {"name": "lanueva_sociedad", "url": "http://www.lanueva.com/news/rss/category/10"},
    {"name": "lpo_ultimasnoticias", "url": "http://www.lapoliticaonline.com.ar/files/rss/ultimasnoticias.xml"},
    {"name": "lpo_politica", "url": "http://www.lapoliticaonline.com.ar/files/rss/politica.xml"},
    {"name": "lpo_economia", "url": "http://www.lapoliticaonline.com.ar/files/rss/economia.xml"},
    {"name": "lpo_ciudad", "url": "http://www.lapoliticaonline.com.ar/files/rss/ciudad.xml"},
    {"name": "lpo_provincia", "url": "http://www.lapoliticaonline.com.ar/files/rss/provincia.xml"},
    {"name": "lpo_conurbano", "url": "http://www.lapoliticaonline.com.ar/files/rss/conurbano.xml"},
    {"name": "lpo_campo", "url": "http://www.lapoliticaonline.com.ar/files/rss/campo.xml"},
    {"name": "letra_p_judiciales", "url": "https://www.letrap.com.ar/rss/pages/judiciales.xml"},
    {"name": "letra_p_ciudad", "url": "https://www.letrap.com.ar/rss/pages/ciudad.xml"},
    {"name": "letra_p_politica", "url": "https://www.letrap.com.ar/rss/pages/politica.xml"},
    {"name": "letra_p_conurbano", "url": "https://www.letrap.com.ar/rss/pages/conurbano.xml"},
    {"name": "letra_p_municipios", "url": "https://www.letrap.com.ar/rss/pages/municipios.xml"},
    {"name": "letra_p_sociedad", "url": "https://www.letrap.com.ar/rss/pages/sociedad.xml"},
    {"name": "letra_p_economia", "url": "https://www.letrap.com.ar/rss/pages/economia.xml"},
    {"name": "diario3", "url": "https://www.diario3.com.ar/feed"}
]

def analizar_feed(feed_info):
    print(f"\nAnalizando feed: {feed_info['name']} - {feed_info['url']}")
    try:
        feed = feedparser.parse(feed_info['url'])
        
        if not feed.entries:
            print(f"  - No se encontraron entradas en el feed")
            return {
                "nombre": feed_info['name'],
                "url": feed_info['url'],
                "estado": "sin entradas",
                "tiene_contenido_completo": False
            }
        
        # Tomar la primera entrada para análisis
        entry = feed.entries[0]
        
        # Mostrar campos disponibles
        print(f"  - Campos disponibles: {list(entry.keys())}")
        
        # Verificar si tiene contenido completo
        tiene_content = 'content' in entry
        tiene_summary = 'summary' in entry
        tiene_summary_detail = 'summary_detail' in entry
        
        print(f"  - ¿Tiene campo 'content'?: {tiene_content}")
        print(f"  - ¿Tiene campo 'summary'?: {tiene_summary}")
        print(f"  - ¿Tiene campo 'summary_detail'?: {tiene_summary_detail}")
        
        # Analizar el contenido
        contenido_muestra = ""
        longitud_contenido = 0
        
        if tiene_content:
            if isinstance(entry.content, list) and len(entry.content) > 0:
                contenido_muestra = entry.content[0].value[:300]
                longitud_contenido = len(entry.content[0].value)
                print(f"  - Longitud del contenido: {longitud_contenido} caracteres")
            else:
                contenido_muestra = str(entry.content)[:300]
                longitud_contenido = len(str(entry.content))
        elif tiene_summary:
            contenido_muestra = entry.summary[:300]
            longitud_contenido = len(entry.summary)
            print(f"  - Longitud del summary: {longitud_contenido} caracteres")
        
        # Determinar si probablemente tiene el artículo completo
        # Criterio: si el contenido es largo (más de 1000 caracteres) o contiene etiquetas HTML de párrafos
        tiene_articulo_completo = longitud_contenido > 1000 or "<p>" in contenido_muestra
        
        print(f"  - Muestra de contenido: {contenido_muestra}...")
        print(f"  - ¿Parece tener el artículo completo?: {tiene_articulo_completo}")
        
        return {
            "nombre": feed_info['name'],
            "url": feed_info['url'],
            "estado": "analizado",
            "campos_disponibles": list(entry.keys()),
            "tiene_content": tiene_content,
            "tiene_summary": tiene_summary,
            "tiene_summary_detail": tiene_summary_detail,
            "longitud_contenido": longitud_contenido,
            "tiene_articulo_completo": tiene_articulo_completo
        }
        
    except Exception as e:
        print(f"  - Error al analizar el feed: {str(e)}")
        return {
            "nombre": feed_info['name'],
            "url": feed_info['url'],
            "estado": "error",
            "error": str(e),
            "tiene_contenido_completo": False
        }

def main():
    resultados = []
    
    print("=== ANÁLISIS DE FEEDS RSS ===\n")
    
    for feed_info in feeds:
        resultado = analizar_feed(feed_info)
        resultados.append(resultado)
    
    print("\n=== RESUMEN DE RESULTADOS ===\n")
    
    for resultado in resultados:
        if resultado["estado"] == "analizado":
            print(f"{resultado['nombre']}: {'CONTIENE artículo completo' if resultado.get('tiene_articulo_completo', False) else 'NO contiene artículo completo'}")
        else:
            print(f"{resultado['nombre']}: {resultado['estado']}")
    
    # Guardar resultados en un archivo JSON
    with open('analisis_feeds.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    
    print("\nResultados guardados en 'analisis_feeds.json'")

if __name__ == "__main__":
    main()