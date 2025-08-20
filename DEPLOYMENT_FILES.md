# 📦 Guía de Archivos para Despliegue en EasyPanel

## ✅ Archivos NECESARIOS para el despliegue

### Archivos principales del sistema
```
├── web_app.py                    # Aplicación Flask principal
├── main.py                       # Procesador principal RSS
├── background_processor.py       # Procesador en segundo plano
├── requirements.txt              # Dependencias Python
├── start.sh                      # Script de inicio
├── .env.example                  # Plantilla de variables de entorno
├── config.yml                    # Configuración del sistema
└── Makefile                      # Comandos útiles
```

### Carpeta app/ (módulos del sistema)
```
app/
├── __init__.py
├── config.py
├── feed_extractor.py
├── feeds.py
├── fetch.py
├── improved_extractor.py
├── matcher.py
├── notifier.py
├── scheduler.py
├── storage.py
├── tasks.py
└── utils.py
```

### Templates HTML
```
templates/
├── base.html
├── dashboard.html
├── feeds.html
├── keywords.html
├── logs.html
└── test.html
```

### Archivos de despliegue
```
├── easypanel-deploy.yml          # Configuración EasyPanel
├── docker-compose.yml            # Docker Compose alternativo
├── Dockerfile                    # Dockerfile alternativo
├── deploy-easypanel.sh           # Script de despliegue
├── EASYPANEL_DEPLOYMENT.md       # Guía completa
├── DEPLOY_QUICK.md               # Guía rápida
└── WEB_INTERFACE.md              # Documentación interfaz
```

## ❌ Archivos que PUEDES OMITIR (desarrollo/testing)

### Scripts de desarrollo y testing
```
├── analizar_feeds.py
├── analyze_pending_articles.py
├── check_articles.py
├── check_content_keywords.py
├── check_content_processing.py
├── check_content_status.py
├── check_keyword_hits.py
├── check_new_mentions.py
├── check_processed_content.py
├── clean_db.py
├── debug_feed_processing.py
├── enable_wal_mode.py
├── generate_performance_report.py
├── improve_content_extraction.py
├── install_dependencies.py
├── install_playwright.py
├── optimizar_extraccion.py
├── probar_feeds_deshabilitados.py
├── probar_optimizacion.py
├── procesar_feeds_deshabilitados.py
├── process_pending_articles.py
├── process_with_playwright.py
├── reset_and_process.py
├── run_as_services.py
├── run_background_processor.py
├── show_hits.py
├── test_app.py
├── test_content_extraction.py
├── test_playwright_extraction.py
├── verificar_estado.py
├── verificar_optimizacion.py
└── verify_content_extraction.py
```

### Archivos de análisis y logs de desarrollo
```
├── analisis_completo.txt
├── analisis_feeds.json
├── analisis_pendientes.txt
├── background_processor.log
└── mentions.db                   # Base de datos local (se crea automáticamente)
```

### Carpetas que puedes omitir
```
├── .pytest_cache/               # Cache de pytest
├── tests/                       # Tests unitarios (opcional)
├── venv/                        # Entorno virtual local
├── data/                        # Datos locales (se crean automáticamente)
└── logs/                        # Logs locales (se crean automáticamente)
```

## 📋 LISTA DE ARCHIVOS PARA COMPRIMIR

### Comando para crear el archivo comprimido:
```bash
# Desde la carpeta del proyecto
tar -czf rss-monitor-deploy.tar.gz \
  --exclude='venv' \
  --exclude='.pytest_cache' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='data' \
  --exclude='logs' \
  --exclude='mentions.db*' \
  --exclude='background_processor.log' \
  --exclude='analisis_*.txt' \
  --exclude='analisis_*.json' \
  --exclude='check_*.py' \
  --exclude='test_*.py' \
  --exclude='verify_*.py' \
  --exclude='debug_*.py' \
  --exclude='install_*.py' \
  --exclude='process_*.py' \
  --exclude='run_*.py' \
  --exclude='show_*.py' \
  --exclude='clean_*.py' \
  --exclude='enable_*.py' \
  --exclude='generate_*.py' \
  --exclude='improve_*.py' \
  --exclude='optimizar_*.py' \
  --exclude='probar_*.py' \
  --exclude='procesar_*.py' \
  --exclude='reset_*.py' \
  --exclude='analizar_*.py' \
  --exclude='analyze_*.py' \
  .
```

### O manualmente incluir solo estos archivos:
```
rss-mentions-monitor/
├── app/                          # Toda la carpeta
├── templates/                    # Toda la carpeta
├── web_app.py
├── main.py
├── background_processor.py
├── requirements.txt
├── start.sh
├── .env.example
├── config.yml
├── Makefile
├── easypanel-deploy.yml
├── docker-compose.yml
├── Dockerfile
├── deploy-easypanel.sh
├── EASYPANEL_DEPLOYMENT.md
├── DEPLOY_QUICK.md
├── WEB_INTERFACE.md
└── README.md
```

## 🎯 Tamaño estimado del archivo comprimido
- **Con todos los archivos**: ~50-100 MB
- **Solo archivos necesarios**: ~5-10 MB

## ⚠️ Notas importantes
1. **NO incluyas** el archivo `.env` si contiene datos sensibles
2. **Las carpetas** `data/`, `logs/` se crean automáticamente en EasyPanel
3. **La base de datos** `mentions.db` se crea automáticamente
4. **El entorno virtual** se instala automáticamente en EasyPanel

---

**Resultado**: Un archivo comprimido limpio y optimizado para despliegue en EasyPanel.