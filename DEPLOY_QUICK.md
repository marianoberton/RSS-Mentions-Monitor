# 🚀 Deployment Rápido en EasyPanel

## 📦 Paso 1: Preparar archivos

```powershell
# Comprimir proyecto (excluir archivos innecesarios)
Compress-Archive -Path . -DestinationPath rss-monitor.zip -Exclude venv,__pycache__,.pytest_cache,*.pyc,.git
```

## ☁️ Paso 2: Subir a VPS

1. Subir `rss-monitor.zip` a tu VPS
2. Extraer: `unzip rss-monitor.zip`

## 🔧 Paso 3: Configurar EasyPanel

### Crear aplicación:
- **Tipo:** Docker Compose
- **Archivo:** `easypanel-deploy.yml`
- **Puerto:** 5000

### Variables de entorno:
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
FLASK_SECRET_KEY=clave_secreta_aleatoria
```

### Dominio:
- Configurar tu dominio/subdominio
- EasyPanel configurará SSL automáticamente

## ✅ Paso 4: Deploy

1. Clic en **"Deploy"**
2. Esperar 2-3 minutos
3. Acceder a `https://tu-dominio.com`

## 🎯 URLs importantes:

- **Dashboard:** `/`
- **Feeds:** `/feeds`
- **Keywords:** `/keywords`
- **Testing:** `/test`
- **Logs:** `/logs`
- **API:** `/api/stats`

## 🔍 Verificar funcionamiento:

1. ✅ Dashboard carga correctamente
2. ✅ Feeds están activos
3. ✅ Keywords configuradas
4. ✅ Test del sistema funciona
5. ✅ Logs se muestran
6. ✅ Notificaciones Telegram funcionan

¡Listo! Tu sistema está funcionando en producción 🎉

---

**💡 Tip:** Si tienes problemas, revisa los logs del container en EasyPanel o accede a `/logs` en la web.