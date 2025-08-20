# RSS Mentions Monitor

🔍 **Monitor de Menciones RSS** - Sistema automatizado para detectar menciones de palabras clave en feeds RSS de medios argentinos.

Este proyecto monitorea feeds RSS para detectar menciones de palabras clave específicas (nombres de políticos), extrae el contenido completo de los artículos y envía alertas a un canal de Telegram. El sistema ha sido optimizado para mayor confiabilidad y rendimiento con una extracción de contenido mejorada y un manejo eficiente de la base de datos.

## 🚀 Despliegue Rápido

### EasyPanel (Recomendado)

1. **Fork este repositorio** en tu cuenta de GitHub
2. **Conecta tu repositorio** a EasyPanel
3. **Configura las variables de entorno** (ver sección de configuración)
4. **Despliega** con un click

### Docker

```bash
git clone https://github.com/tu-usuario/rss-mentions-monitor.git
cd rss-mentions-monitor
cp .env.example .env
# Edita .env con tus valores
docker-compose up -d
```

## Características

- Monitoreo de múltiples feeds RSS configurables.
- Búsqueda de palabras clave en títulos, resúmenes y contenido completo de artículos.
- Extracción inteligente de contenido que detecta feeds con contenido completo y extrae directamente cuando es posible.
- Extracción robusta de contenido con múltiples selectores CSS y mecanismos de reintento para feeds sin contenido completo.
- Extracción avanzada de contenido usando Playwright para sitios con JavaScript intensivo y paywalls (opcional).
- Procesamiento en segundo plano de artículos pendientes con reintentos automáticos.
- Base de datos SQLite optimizada con modo WAL para operaciones concurrentes.
- Deduplicación de artículos para evitar notificaciones repetidas.
- Persistencia de datos en una base de datos SQLite.
- Envío de notificaciones a un canal de Telegram.
- Resumen horario con estadísticas de procesamiento y menciones.
- Notificaciones específicas para menciones importantes (Liberman y Coria).
- Ejecución programada usando APScheduler con frecuencia configurable.
- Interfaz de línea de comandos para generar informes y estadísticas de rendimiento.
- Containerizable con Docker.

## Configuración

### 1. Crear un Bot de Telegram

1. Abre Telegram y busca al bot `BotFather`.
2. Inicia una conversación con `BotFather` y envía el comando `/newbot`.
3. Sigue las instrucciones para elegir un nombre y un nombre de usuario para tu bot.
4. `BotFather` te proporcionará un token para tu bot. Copia este token.

### 2. Obtener tu ID de Chat de Telegram

1. Después de crear tu bot, búscalo en Telegram y envíale un mensaje.
2. Abre tu navegador y ve a la siguiente URL, reemplazando `<TuTokenDeBOT>` con el token que recibiste de `BotFather`:

   ```
   https://api.telegram.org/bot<TuTokenDeBOT>/getUpdates
   ```

3. Busca el campo `"chat": {"id": ...}` en la respuesta JSON. El número es tu ID de chat.

### 3. Configurar la Aplicación

1. Crea un archivo `.env` en la raíz del proyecto copiando el archivo `.env.example`:

   ```bash
   cp .env.example .env
   ```

2. Abre el archivo `.env` y completa las siguientes variables:

   ```
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui
   LOG_LEVEL=INFO
   SQLITE_PATH=./data/rss_monitor.db
   TZ=America/Argentina/Buenos_Aires
   ```

### 4. Configurar el archivo config.yml

Edita el archivo `config.yml` para configurar los feeds RSS y las palabras clave:

```yaml
timezone: "America/Argentina/Buenos_Aires"
interval_minutes: 60  # Frecuencia de ejecución en minutos
request_timeout_sec: 15
feeds:
  - {name: "infocielo", url: "https://www.infocielo.com/feed", enabled: true}
  - {name: "labrujula24", url: "https://www.labrujula24.com/feed/", enabled: true}
  # Añadir más feeds según sea necesario
 
keywords:
  - "Oscar Liberman"
  - "Gustavo Coria"
  - "Javier Milei"
```

    ## Despliegue en VPS

### Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Acceso a un VPS con sistema operativo Linux (Ubuntu/Debian recomendado)

### Pasos para el despliegue

1. **Preparar el entorno en el VPS**

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3 python3-pip python3-venv git

# Crear directorio para la aplicación
mkdir -p ~/apps
cd ~/apps

# Clonar el repositorio
git clone https://github.com/tu-usuario/rss-mentions-monitor.git
cd rss-mentions-monitor

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

2. **Configurar las variables de entorno**

Crea un archivo `.env` en el directorio del proyecto con las variables mencionadas anteriormente.

3. **Crear un servicio systemd para ejecutar la aplicación como demonio**

```bash
sudo nano /etc/systemd/system/rss-monitor.service
```

Añade el siguiente contenido (ajusta las rutas según tu configuración):

```ini
[Unit]
Description=RSS Mentions Monitor
After=network.target

[Service]
User=tu_usuario
WorkingDirectory=/home/tu_usuario/apps/rss-mentions-monitor
EnvironmentFile=/home/tu_usuario/apps/rss-mentions-monitor/.env
ExecStart=/home/tu_usuario/apps/rss-mentions-monitor/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=rss-monitor

[Install]
WantedBy=multi-user.target
```

4. **Habilitar y iniciar el servicio**

```bash
sudo systemctl daemon-reload
sudo systemctl enable rss-monitor.service
sudo systemctl start rss-monitor.service
```

5. **Verificar el estado del servicio**

```bash
sudo systemctl status rss-monitor.service
```

6. **Ver los logs**

```bash
sudo journalctl -u rss-monitor.service -f
```

## Mantenimiento

### Actualización del código

```bash
cd ~/apps/rss-mentions-monitor
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart rss-monitor.service
```

### Backup de la base de datos

```bash
# Crear directorio de backups
mkdir -p ~/backups

# Copiar la base de datos
cp ~/apps/rss-mentions-monitor/data/rss_monitor.db ~/backups/rss_monitor_$(date +%Y%m%d).db
```

### Automatizar backups

Añade una tarea cron para hacer backups diarios:

```bash
crontab -e
```

Añade la siguiente línea:

```
0 0 * * * cp ~/apps/rss-mentions-monitor/data/rss_monitor.db ~/backups/rss_monitor_$(date +%Y%m%d).db
```

## Solución de problemas

- **El servicio no inicia**: Verifica los logs con `sudo journalctl -u rss-monitor.service`
- **No se reciben notificaciones**: Asegúrate de que el token y chat_id son correctos
- **Error de permisos**: Verifica que el usuario tiene permisos de escritura en el directorio de datos
    

### 4. (Optional) Install Playwright for Advanced Content Extraction

For sites with JavaScript-heavy content or paywalls, you can use Playwright as an alternative extraction method:

1. Run the Playwright installation script:

   ```bash
   python install_playwright.py
   ```

   This will install the Playwright package and the Chromium browser.

2. Test the Playwright extraction with a specific URL:

   ```bash
   python test_playwright_extraction.py https://example.com/article
   ```

3. Process pending articles with Playwright:

   ```bash
   python process_with_playwright.py --limit 20
   ```

   You can also filter by site:

   ```bash
   python process_with_playwright.py --site diario3.com.ar
   ```

3.  (Optional) Modify the `config.yml` file to change the RSS feeds, keywords, and other settings.

## Optimizations and New Components

### Improved Content Extraction

- `improved_extractor.py`: Enhanced article content extraction with multiple CSS selectors and robust error handling.
- Retry mechanism with exponential backoff and random delays for more reliable extraction.
- Smart feed detection that identifies feeds containing full article content and extracts directly from the feed.
- `feed_extractor.py`: Module for extracting content directly from RSS feeds when available, reducing resource usage and improving performance.

### Background Processing

- `background_processor.py`: Continuously processes pending articles in the background.
- Safe database operations with retry mechanisms to handle database locks.
- Random delays between processing to prevent resource contention.

### Database Optimizations

- `enable_wal_mode.py`: Enables SQLite WAL (Write-Ahead Logging) mode for concurrent read/write operations.
- Additional optimizations for better performance:
  - PRAGMA synchronous=NORMAL: Reduces synchronization overhead
  - PRAGMA temp_store=MEMORY: Stores temporary tables in memory
  - PRAGMA mmap_size: Uses memory mapping for faster access
  - PRAGMA cache_size: Increases cache size for better performance

### Monitoring and Reporting

- `check_content_status.py`: Verifies article processing status and ensures no mentions are lost.
- `generate_performance_report.py`: Provides detailed statistics on processing performance.

### Service Management

- `run_as_services.py`: Runs the RSS monitor and background processor as services with automatic restart.

## Running the Application

### Standard Execution

Run the main application to monitor RSS feeds:

```bash
python main.py
```

### Background Processing

Run the background processor to continuously process pending articles:

```bash
python background_processor.py
```

### Run as Services

Run both components as services with automatic restart:

```bash
python run_as_services.py
```

### Utility Scripts

Enable WAL mode for the database (recommended before first run):

```bash
python enable_wal_mode.py
```

Check content processing status:

```bash
python check_content_status.py
```

Generate performance report:

```bash
python generate_performance_report.py
```

### Locally

1.  Create a virtual environment and install the dependencies:

    ```bash
    make venv
    . venv/bin/activate
    pip install -r requirements.txt
    ```

2.  Run the application:

    ```bash
    make run
    ```

### With Docker

1.  Build the Docker image:

    ```bash
    make docker-build
    ```

2.  Run the application using Docker Compose:

    ```bash
    make docker-run
    ```

## Generating Reports

You can generate a report of the mentions found in the last 24 hours by running:

```bash
python -m app.report --since 24h
```

To send the report to Telegram, use the `--telegram` flag:

```bash
python -m app.report --since 24h --telegram
```

## Alternative: Cron Job

If you prefer not to use the internal scheduler, you can run the main task as a cron job. Add the following line to your crontab:

```cron
*/60 * * * * cd /srv/rss-mentions-monitor && /usr/bin/python3 main.py >> /var/log/rss-monitor.cron 2>&1
```