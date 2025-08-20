# 🤖 Prompt para ChatGPT - Asistencia en Despliegue EasyPanel

## Copia y pega este prompt en ChatGPT:

---

**Eres un experto en despliegue de aplicaciones Python Flask en EasyPanel. Necesito tu ayuda para desplegar un sistema de monitoreo RSS.**

**CONTEXTO DEL PROYECTO:**
- Sistema de monitoreo RSS con interfaz web Flask
- Base de datos SQLite
- Scraping con Playwright
- Procesamiento en segundo plano
- Ya tengo todos los archivos listos para desplegar

**ARCHIVOS PRINCIPALES:**
- `web_app.py` (Flask app principal)
- `main.py` (procesador RSS)
- `background_processor.py` (procesador en segundo plano)
- `easypanel-deploy.yml` (configuración EasyPanel)
- `requirements.txt` (dependencias)
- `start.sh` (script de inicio)
- Carpeta `app/` (módulos del sistema)
- Carpeta `templates/` (HTML templates)

**CONFIGURACIÓN EASYPANEL:**
- Tipo: Docker Compose
- Puerto: 5000
- Variables de entorno necesarias:
  - `RSS_FEEDS`: Lista de URLs RSS separadas por comas
  - `KEYWORDS`: Palabras clave separadas por comas
  - `FLASK_ENV`: production

**MI SITUACIÓN ACTUAL:**
- Tengo un VPS con EasyPanel funcionando
- Ya tengo otros servicios corriendo (n8n, Chatwoot)
- Tengo el archivo comprimido del proyecto listo
- Necesito ayuda paso a paso para el despliegue

**LO QUE NECESITO:**
1. Guía paso a paso para subir y configurar en EasyPanel
2. Ayuda con cualquier error que pueda surgir
3. Verificación de que todo funcione correctamente
4. Consejos de monitoreo y mantenimiento

**PREGUNTA INICIAL:** [Aquí describe tu situación específica o pregunta actual]

**Por favor, ayúdame con instrucciones claras y específicas para EasyPanel. Si encuentro errores, te los compartiré para que me ayudes a resolverlos.**

---

## 📝 Ejemplos de preguntas específicas que puedes hacer:

### Durante la subida:
```
"Subí mi archivo comprimido al VPS pero no sé cómo extraerlo correctamente. 
¿Cuál es el comando exacto para extraer y colocar los archivos en la ubicación correcta?"
```

### Durante la configuración en EasyPanel:
```
"Estoy en EasyPanel creando un nuevo servicio. Seleccioné 'Docker Compose' pero 
no sé exactamente qué poner en cada campo. ¿Me puedes guiar paso a paso?"
```

### Para variables de entorno:
```
"Necesito configurar las variables de entorno en EasyPanel. Tengo estas URLs RSS: 
[lista tus URLs] y estas keywords: [lista tus keywords]. 
¿Cómo las formato correctamente?"
```

### Para errores específicos:
```
"Mi servicio no inicia y veo este error en los logs: [copia el error exacto]. 
¿Qué puede estar pasando y cómo lo soluciono?"
```

### Para verificación:
```
"Mi servicio dice que está corriendo pero cuando accedo a la URL no veo nada. 
¿Cómo verifico que todo esté funcionando correctamente?"
```

### Para configuración de dominio:
```
"Quiero configurar un dominio personalizado para mi aplicación. 
Tengo el dominio [tu-dominio.com]. ¿Cómo lo configuro en EasyPanel?"
```

## 🔧 Información técnica para compartir si es necesario:

### Estructura del proyecto:
```
rss-mentions-monitor/
├── app/                 # Módulos Python
├── templates/           # Templates HTML
├── web_app.py          # Flask app
├── main.py             # Procesador RSS
├── easypanel-deploy.yml # Configuración
└── requirements.txt    # Dependencias
```

### Puertos y servicios:
- **Puerto interno**: 5000 (Flask)
- **Healthcheck**: `/api/stats`
- **URLs importantes**:
  - `/` (Dashboard)
  - `/feeds` (Gestión RSS)
  - `/keywords` (Gestión keywords)
  - `/logs` (Logs del sistema)

### Dependencias principales:
- Python 3.11
- Flask
- SQLite
- Playwright
- APScheduler

---

**💡 Tip**: Copia este prompt completo y pégalo en ChatGPT. Luego reemplaza "[PREGUNTA INICIAL]" con tu situación específica actual.