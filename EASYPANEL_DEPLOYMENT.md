# 🚀 Guía de Deployment en EasyPanel

## Opción 1: Deployment Directo (Recomendado)

### Paso 1: Preparar archivos

1. **Comprimir el proyecto:**
   ```bash
   # En Windows (PowerShell)
   Compress-Archive -Path . -DestinationPath rss-monitor.zip -Exclude venv,__pycache__,.pytest_cache,*.pyc,.git
   
   # En Linux/Mac
   tar -czf rss-monitor.tar.gz --exclude='venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' --exclude='.git' .
   ```

2. **Subir al VPS:**
   - Usar SFTP, SCP o el file manager de EasyPanel
   - Extraer en el directorio de tu elección

### Paso 2: Configurar en EasyPanel

1. **Crear nueva aplicación:**
   - Ir a EasyPanel → Applications → Create
   - Nombre: `rss-mentions-monitor`
   - Tipo: **Docker Compose**

2. **Configuración Docker Compose:**
   - Usar el archivo `easypanel-deploy.yml`
   - O copiar esta configuración:

```yaml
version: '3.8'

services:
  rss-monitor:
    image: python:3.11-slim
    container_name: rss-mentions-monitor
    working_dir: /app
    ports:
      - "5000:5000"
    volumes:
      - .:/app
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - TZ=America/Argentina/Buenos_Aires
      - FLASK_ENV=production
      - FLASK_APP=web_app.py
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
    command: >
      bash -c "
        apt-get update && apt-get install -y gcc curl &&
        pip install --no-cache-dir -r requirements.txt &&
        chmod +x start.sh &&
        ./start.sh
      "
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5000 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

3. **Variables de entorno:**
   ```env
   TELEGRAM_BOT_TOKEN=tu_token_de_telegram
   TELEGRAM_CHAT_ID=tu_chat_id
   FLASK_SECRET_KEY=una_clave_secreta_muy_aleatoria_y_segura
   TZ=America/Argentina/Buenos_Aires
   ```

4. **Configurar puerto:**
   - Puerto interno: `5000`
   - Puerto externo: `5000` (o el que prefieras)

5. **Configurar dominio:**
   - Agregar tu dominio o subdominio
   - EasyPanel configurará automáticamente SSL

### Paso 3: Deploy

1. **Hacer deploy:**
   - Clic en "Deploy"
   - Esperar que se construya e inicie (puede tomar 2-3 minutos)

2. **Verificar funcionamiento:**
   - Acceder a `https://tu-dominio.com`
   - Verificar que aparece el dashboard
   - Revisar logs en `/logs`

## Opción 2: Usando imagen Docker personalizada

### Si prefieres usar Docker Hub:

1. **Construir imagen:**
   ```bash
   docker build -t tu-usuario/rss-monitor .
   docker push tu-usuario/rss-monitor
   ```

2. **En EasyPanel:**
   - Tipo: Docker Image
   - Imagen: `tu-usuario/rss-monitor:latest`
   - Puerto: 5000
   - Variables de entorno como arriba

## 🔧 Configuración Post-Deployment

### Verificar funcionamiento:

1. **Dashboard:** `https://tu-dominio.com`
2. **API Stats:** `https://tu-dominio.com/api/stats`
3. **Logs:** `https://tu-dominio.com/logs`

### Configurar feeds y keywords:

1. **Ir a `/feeds`:**
   - Verificar que los feeds están activos
   - Probar feeds individuales

2. **Ir a `/keywords`:**
   - Verificar palabras clave configuradas
   - Agregar nuevas si es necesario

3. **Probar sistema:**
   - Ir a `/test`
   - Ejecutar test completo
   - Verificar que funciona correctamente

## 🛠️ Troubleshooting

### Problemas comunes:

1. **Container no inicia:**
   ```bash
   # Ver logs del container
   docker logs rss-mentions-monitor
   ```

2. **Error de permisos:**
   ```bash
   # Dar permisos a directorios
   chmod -R 755 data logs
   ```

3. **Variables de entorno no funcionan:**
   - Verificar que el archivo `.env` existe
   - Verificar sintaxis de variables
   - No usar espacios alrededor del `=`

4. **Puerto no accesible:**
   - Verificar configuración de firewall
   - Verificar que EasyPanel tiene el puerto configurado

### Comandos útiles:

```bash
# Ver estado del container
docker ps

# Ver logs en tiempo real
docker logs -f rss-mentions-monitor

# Acceder al container
docker exec -it rss-mentions-monitor bash

# Reiniciar container
docker restart rss-mentions-monitor

# Ver uso de recursos
docker stats rss-mentions-monitor
```

## 📊 Monitoreo

### Health Checks:
- EasyPanel verificará automáticamente cada 30 segundos
- URL de health check: `http://localhost:5000`

### Logs:
- Accesibles via web: `https://tu-dominio.com/logs`
- Archivo físico: `./logs/app.log`

### Backup:
```bash
# Backup de base de datos
docker exec rss-mentions-monitor cp /app/data/mentions.db /app/backup/

# Backup completo
tar -czf backup-$(date +%Y%m%d).tar.gz data logs config.yml
```

## 🔒 Seguridad

### Recomendaciones:

1. **Cambiar clave secreta:**
   ```env
   FLASK_SECRET_KEY=genera_una_clave_muy_aleatoria_y_segura
   ```

2. **Usar HTTPS:**
   - EasyPanel configura automáticamente SSL
   - Verificar que el certificado es válido

3. **Restricción de acceso (opcional):**
   - Configurar autenticación básica en EasyPanel
   - Usar VPN si es necesario

4. **Backup regular:**
   - Configurar backup automático de la base de datos
   - Guardar configuraciones importantes

## 🎯 URLs Importantes

Una vez desplegado:

- **Dashboard:** `https://tu-dominio.com/`
- **Feeds:** `https://tu-dominio.com/feeds`
- **Keywords:** `https://tu-dominio.com/keywords`
- **Testing:** `https://tu-dominio.com/test`
- **Logs:** `https://tu-dominio.com/logs`
- **API Stats:** `https://tu-dominio.com/api/stats`

## ✅ Checklist Final

- [ ] Archivos subidos al VPS
- [ ] Variables de entorno configuradas
- [ ] Container iniciado correctamente
- [ ] Dashboard accesible
- [ ] Feeds funcionando
- [ ] Keywords configuradas
- [ ] Notificaciones de Telegram funcionando
- [ ] Logs visibles
- [ ] Health checks pasando
- [ ] SSL configurado
- [ ] Backup configurado

¡Tu sistema RSS Mentions Monitor está listo para producción! 🎉