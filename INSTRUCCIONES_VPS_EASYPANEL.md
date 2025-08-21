# Instrucciones para VPS EasyPanel - RSS Mentions Monitor

## Configuración Actual

### Variables de Entorno Configuradas
```
TELEGRAM_BOT_TOKEN=8433040986:AAHvugen7amF6vwd8cbTB4NOaNVSqEPelnw
TELEGRAM_CHAT_ID=1880232778
LOG_LEVEL=INFO
SQLITE_PATH=data/mentions.db
TZ=America/Argentina/Buenos_Aires
```

### Estado del Monitoreo
- ✅ **Andres de Leo**: **NOTIFICACIONES IMPORTANTES** activas
- ✅ **Oscar Liberman**: **NOTIFICACIONES IMPORTANTES** activas  
- ✅ **Gustavo Coria**: **NOTIFICACIONES IMPORTANTES** activas
- ✅ **Javier Milei**: Monitoreo estándar activo
- ✅ **Efectividad**: 82% (EXCELENTE)
- ✅ **Timezone**: Argentina/Buenos_Aires
- ✅ **Interfaz Web**: Herramientas de diagnóstico disponibles

### 🛠️ Nueva Interfaz Web de Herramientas

**¡IMPORTANTE!** Ahora puedes ejecutar todas las herramientas de diagnóstico desde la interfaz web, sin necesidad de usar la consola.

**Acceso:** `http://tu-dominio.com/tools`

**Herramientas Disponibles:**
- 📊 Verificar Efectividad
- 🔍 Verificar Estado  
- ✅ Verificar Solución
- 👤 Verificar Andres de Leo
- 🚀 Verificar Optimización
- ⚙️ Procesar Artículos Pendientes
- 🔄 Procesar Todos los Feeds
- 📈 Generar Reporte de Rendimiento
- 🔬 Analizar Efectividad
- 📄 Verificar Estado de Contenido

**Ventajas:**
- ✅ Sin comandos de consola
- ✅ Interfaz gráfica intuitiva
- ✅ Resultados formateados
- ✅ Ejecución segura con timeouts
- ✅ Filtros por categoría
- ✅ Copiar resultados al portapapeles

## Pasos para Verificación en EasyPanel

### 1. Acceder a la Consola Docker

En EasyPanel:
1. Ve a tu servicio RSS Mentions Monitor
2. Busca la opción "Console" o "Terminal"
3. Haz clic para abrir la consola del contenedor

### 2. Comandos de Verificación Rápida

Copia y pega estos comandos uno por uno:

```bash
# Verificar que estás en el directorio correcto
pwd
ls -la

# Verificar variables de entorno
env | grep -E "TELEGRAM|LOG|SQLITE|TZ"

# Verificar base de datos
ls -la data/
sqlite3 data/mentions.db "PRAGMA integrity_check;"
sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits;"

# Verificar menciones de Andres de Leo
sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits WHERE keyword='Andres de Leo';"

# Verificar efectividad
sqlite3 data/mentions.db "SELECT COUNT(DISTINCT url) as unicas, COUNT(*) as total, ROUND((COUNT(DISTINCT url) * 100.0 / COUNT(*)), 1) as efectividad FROM hits;"

# Verificar logs
tail -n 10 logs/app.log

# Verificar salud del servicio
curl http://localhost:5000/health
```

### 3. Ejecutar Diagnóstico Completo

```bash
# Ejecutar script de diagnóstico
python diagnostico_vps.py

# Ejecutar análisis de efectividad
python verificar_efectividad.py
```

### 4. Comandos de Monitoreo Continuo

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Monitorear menciones nuevas
watch -n 30 'sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits WHERE created_at > datetime(\"now\", \"-1 hour\");"'

# Ver últimas menciones
sqlite3 data/mentions.db "SELECT keyword, title, created_at FROM hits ORDER BY created_at DESC LIMIT 5;"
```

## Solución de Problemas Comunes

### Si la Base de Datos está Corrupta

```bash
# Crear backup
cp data/mentions.db data/backup_$(date +%Y%m%d).db

# Recuperar datos
sqlite3 data/mentions.db ".recover" > backup.sql
rm data/mentions.db
sqlite3 data/mentions.db < backup.sql
```

### Si No Hay Menciones Recientes

```bash
# Verificar procesos
ps aux | grep python

# Verificar conectividad
curl -I https://www.lanacion.com.ar/
curl -I https://www.clarin.com/

# Verificar configuración
cat config.yml | grep -A 5 keywords
cat config.yml | grep -A 10 feeds
```

### Si Hay Errores en Logs

```bash
# Ver errores recientes
grep -i error logs/app.log | tail -10
grep -i exception logs/app.log | tail -5

# Limpiar logs si están muy grandes
echo "" > logs/app.log
echo "" > logs/error.log
```

## Comandos de Mantenimiento

### Desde la Consola de EasyPanel (Host)

```bash
# Reiniciar contenedor
docker restart <nombre_contenedor>

# Ver logs del contenedor
docker logs <nombre_contenedor> --tail 50

# Ver uso de recursos
docker stats <nombre_contenedor>

# Backup de base de datos
docker cp <nombre_contenedor>:/app/data/mentions.db ./backup_$(date +%Y%m%d).db
```

## Métricas de Rendimiento Esperadas

### Con Efectividad del 82%
- **URLs únicas**: ~82 de cada 100 menciones
- **Duplicados**: ~18 de cada 100 menciones
- **Andres de Leo**: Menciones regulares según actividad mediática

### Frecuencia de Menciones Esperada
- **Diaria**: 5-20 menciones (dependiendo de la actividad)
- **Semanal**: 35-140 menciones
- **Mensual**: 150-600 menciones

## Alertas y Monitoreo

### Indicadores de Problemas
- ❌ Efectividad < 70%
- ❌ Sin menciones en 24h
- ❌ Errores en logs
- ❌ Base de datos corrupta
- ❌ Servicio no responde en /health

### Indicadores de Funcionamiento Normal
- ✅ Efectividad > 80%
- ✅ Menciones diarias regulares
- ✅ Logs sin errores
- ✅ Base de datos íntegra
- ✅ Servicio responde OK en /health

## Contacto y Soporte

Si encuentras problemas:
1. Ejecuta `python diagnostico_vps.py`
2. Revisa los logs con `tail -n 50 logs/app.log`
3. Verifica la conectividad externa
4. Reinicia el contenedor si es necesario

## Archivos de Diagnóstico Incluidos

- `diagnostico_vps.py`: Diagnóstico completo del sistema
- `verificar_efectividad.py`: Análisis específico de efectividad
- `comandos_consola_docker.sh`: Script con comandos útiles
- `comandos_docker_vps.md`: Guía completa de comandos Docker

¡Tu sistema está configurado correctamente con 82% de efectividad!