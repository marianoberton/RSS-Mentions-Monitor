# Despliegue en EasyPanel

Esta guía te ayudará a desplegar el RSS Mentions Monitor en EasyPanel.

## 📋 Requisitos Previos

1. **Bot de Telegram configurado**:
   - Crear un bot con @BotFather
   - Obtener el token del bot
   - Obtener el chat ID donde se enviarán las notificaciones

2. **Repositorio Git**:
   - El código debe estar en un repositorio Git accesible
   - Asegúrate de que todos los archivos estén committeados

## 🚀 Pasos para Desplegar

### 1. Configurar Variables de Entorno

En EasyPanel, configura las siguientes variables de entorno:

```
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
TZ=America/Argentina/Buenos_Aires
FLASK_ENV=production
FLASK_APP=web_app.py
PYTHONPATH=/app
```

### 2. Configurar el Servicio

**Tipo de Aplicación**: Docker

**Configuración del Contenedor**:
- **Puerto**: 5000
- **Dockerfile**: Usar el Dockerfile incluido en el repositorio
- **Build Context**: Raíz del repositorio

### 3. Configurar Volúmenes (Opcional)

Para persistir datos entre reinicios:

```
/app/data -> Volumen persistente para la base de datos
/app/logs -> Volumen persistente para logs
```

### 4. Configurar Health Check

```
URL: http://localhost:5000
Intervalo: 30s
Timeout: 10s
Reintentos: 3
```

## 📁 Estructura del Proyecto

```
rss-mentions-monitor/
├── app/                    # Código principal
├── config.yml             # Configuración de feeds y keywords
├── Dockerfile             # Configuración de Docker
├── docker-compose.yml     # Para desarrollo local
├── start.sh              # Script de inicio
├── requirements.txt      # Dependencias Python
├── .env.example          # Ejemplo de variables de entorno
└── DEPLOY.md            # Esta guía
```

## 🔧 Configuración Post-Despliegue

### 1. Verificar el Funcionamiento

- Accede a `https://tu-dominio.com` para ver la interfaz web
- Verifica que aparezcan los feeds configurados
- Revisa los logs para confirmar que no hay errores

### 2. Configurar Keywords

Edita el archivo `config.yml` para configurar:
- Feeds RSS a monitorear
- Keywords a buscar
- Configuraciones específicas

### 3. Probar Notificaciones

- Publica un artículo de prueba con una keyword
- Verifica que llegue la notificación a Telegram
- Revisa la interfaz web para confirmar la detección

## 🛠️ Solución de Problemas

### El contenedor no inicia
- Verifica que todas las variables de entorno estén configuradas
- Revisa los logs del contenedor en EasyPanel
- Confirma que el puerto 5000 esté expuesto

### No llegan notificaciones
- Verifica el token del bot de Telegram
- Confirma el chat ID
- Revisa que el bot tenga permisos para enviar mensajes

### La interfaz web no carga
- Verifica que el puerto 5000 esté mapeado correctamente
- Confirma que el health check esté pasando
- Revisa los logs de Flask

## 📊 Monitoreo

La aplicación incluye:
- **Health check endpoint**: `/health`
- **Interfaz web**: `/` (dashboard principal)
- **API de menciones**: `/mentions` (datos JSON)
- **Logs estructurados**: Disponibles en el contenedor

## 🔄 Actualizaciones

Para actualizar la aplicación:
1. Haz push de los cambios al repositorio
2. En EasyPanel, ve a la aplicación
3. Haz clic en "Rebuild" o "Redeploy"
4. Espera a que se complete el despliegue

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs del contenedor
2. Verifica la configuración de variables de entorno
3. Confirma que el repositorio esté actualizado
4. Prueba el despliegue local con `docker-compose up`

---

✅ **¡Tu RSS Mentions Monitor está listo para producción!**