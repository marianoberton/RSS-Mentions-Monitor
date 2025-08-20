# Interfaz Web para RSS Mentions Monitor

Esta interfaz web proporciona una forma fácil de administrar y monitorear el sistema RSS Mentions Monitor.

## Características

### 🎯 Dashboard Principal
- Estadísticas en tiempo real del sistema
- Menciones recientes detectadas
- Estado de feeds y palabras clave
- Gráficos y métricas de rendimiento

### 📡 Gestión de Feeds RSS
- Agregar nuevos feeds RSS
- Habilitar/deshabilitar feeds existentes
- Probar feeds individuales
- Visualizar estado de todos los feeds

### 🏷️ Gestión de Palabras Clave
- Agregar nuevas palabras clave
- Eliminar palabras clave existentes
- Visualizar tipos de monitoreo:
  - **Milei**: Solo aparece en resúmenes horarios
  - **Oscar Liberman, Gustavo Coria**: Notificaciones importantes
  - **Otras**: Monitoreo estándar

### 🧪 Testing del Sistema
- Ejecutar test completo del sistema
- Probar feeds individuales
- Monitorear estado de ejecución
- Revisar resultados en tiempo real

### 📋 Visualización de Logs
- Ver logs del sistema en tiempo real
- Filtrar por nivel de log (ERROR, WARNING, INFO, etc.)
- Búsqueda de texto en logs
- Auto-refresh automático

## Deployment en EasyPanel

### Opción 1: Docker Compose (Recomendado)

1. **Subir archivos al VPS:**
   ```bash
   # Comprimir el proyecto
   tar -czf rss-monitor.tar.gz .
   
   # Subir al VPS
   scp rss-monitor.tar.gz user@your-vps:/path/to/deployment/
   
   # En el VPS, extraer
   tar -xzf rss-monitor.tar.gz
   ```

2. **Configurar en EasyPanel:**
   - Crear nueva aplicación
   - Tipo: Docker Compose
   - Subir el archivo `docker-compose.yml`
   - Puerto: 5000
   - Dominio: tu-dominio.com

3. **Variables de entorno necesarias:**
   ```env
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   TELEGRAM_CHAT_ID=tu_chat_id_aqui
   FLASK_SECRET_KEY=clave_secreta_para_flask
   TZ=America/Argentina/Buenos_Aires
   ```

### Opción 2: Dockerfile

1. **En EasyPanel:**
   - Crear nueva aplicación
   - Tipo: Docker
   - Usar Dockerfile existente
   - Puerto: 5000

2. **Comando de construcción:**
   ```bash
   docker build -t rss-monitor .
   docker run -d -p 5000:5000 --name rss-monitor \
     -e TELEGRAM_BOT_TOKEN=tu_token \
     -e TELEGRAM_CHAT_ID=tu_chat_id \
     -v ./data:/app/data \
     -v ./logs:/app/logs \
     rss-monitor
   ```

### Configuración de Proxy Reverso

En EasyPanel, configurar el proxy reverso:

```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Acceso a la Interfaz

Una vez desplegado, accede a:
- **URL local**: http://localhost:5000
- **URL pública**: https://tu-dominio.com

### Páginas disponibles:
- `/` - Dashboard principal
- `/feeds` - Gestión de feeds RSS
- `/keywords` - Gestión de palabras clave
- `/test` - Testing del sistema
- `/logs` - Visualización de logs
- `/api/stats` - API de estadísticas (JSON)

## Seguridad

### Recomendaciones para producción:

1. **Cambiar la clave secreta:**
   ```env
   FLASK_SECRET_KEY=una_clave_muy_segura_y_aleatoria
   ```

2. **Configurar HTTPS:**
   - EasyPanel maneja automáticamente SSL/TLS
   - Asegúrate de que el dominio esté configurado correctamente

3. **Restricción de acceso:**
   - Considera agregar autenticación básica
   - Usar VPN o restricción por IP si es necesario

4. **Backup de datos:**
   ```bash
   # Backup automático de la base de datos
   docker exec rss-monitor cp /app/data/mentions.db /app/backup/
   ```

## Monitoreo y Mantenimiento

### Logs del contenedor:
```bash
# Ver logs en tiempo real
docker logs -f rss-mentions-monitor

# Ver logs específicos
docker logs rss-mentions-monitor --since 1h
```

### Health Check:
El contenedor incluye un health check que verifica:
- Disponibilidad de la interfaz web (puerto 5000)
- Estado del monitor RSS
- Conectividad de la base de datos

### Reinicio automático:
El contenedor está configurado con `restart: unless-stopped` para reiniciarse automáticamente en caso de fallos.

## Troubleshooting

### Problemas comunes:

1. **Puerto 5000 no accesible:**
   - Verificar que EasyPanel tenga el puerto configurado
   - Revisar firewall del VPS

2. **Error de base de datos:**
   - Verificar permisos del directorio `/app/data`
   - Revisar logs para errores específicos

3. **Feeds no se procesan:**
   - Verificar conectividad a internet del contenedor
   - Revisar configuración de feeds en `/feeds`

4. **Notificaciones no funcionan:**
   - Verificar variables de entorno de Telegram
   - Probar bot de Telegram manualmente

### Comandos útiles:

```bash
# Reiniciar solo la interfaz web
docker exec rss-monitor pkill -f flask

# Acceder al contenedor
docker exec -it rss-mentions-monitor bash

# Ver uso de recursos
docker stats rss-mentions-monitor

# Backup completo
docker exec rss-monitor tar -czf /tmp/backup.tar.gz /app/data /app/logs
docker cp rss-mentions-monitor:/tmp/backup.tar.gz ./backup.tar.gz
```

## Desarrollo Local

Para desarrollo local:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar solo la interfaz web
export FLASK_APP=web_app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000

# En otra terminal, ejecutar el monitor
python main.py
```

## API Endpoints

### GET /api/stats
Retorna estadísticas del sistema en formato JSON:

```json
{
  "total_articles": 1250,
  "total_hits": 45,
  "success_rate": 98.5,
  "keyword_stats": {
    "Milei": 30,
    "Oscar Liberman": 8,
    "Gustavo Coria": 7
  }
}
```

Este endpoint es útil para integraciones externas o monitoreo automatizado.