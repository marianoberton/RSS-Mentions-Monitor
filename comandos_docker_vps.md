# Comandos de Diagnóstico para Docker en VPS EasyPanel

## 1. Verificar Estado del Contenedor

```bash
# Ver contenedores en ejecución
docker ps

# Ver todos los contenedores (incluidos detenidos)
docker ps -a

# Ver logs del contenedor
docker logs <container_name> --tail 50

# Ver logs en tiempo real
docker logs <container_name> -f
```

## 2. Acceder al Contenedor

```bash
# Entrar al contenedor en modo interactivo
docker exec -it <container_name> /bin/bash

# O si bash no está disponible
docker exec -it <container_name> /bin/sh
```

## 3. Comandos Dentro del Contenedor

Una vez dentro del contenedor:

```bash
# Verificar variables de entorno
env | grep -E "TELEGRAM|LOG|SQLITE|TZ"

# Ejecutar diagnóstico
python diagnostico_vps.py

# Verificar estructura de archivos
ls -la
ls -la data/
ls -la logs/

# Verificar base de datos
sqlite3 data/mentions.db ".schema"
sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits;"
sqlite3 data/mentions.db "PRAGMA integrity_check;"

# Ver logs recientes
tail -n 20 logs/app.log
tail -f logs/app.log  # En tiempo real

# Verificar procesos
ps aux | grep python

# Verificar conectividad
curl -I https://www.lanacion.com.ar/
curl http://localhost:5000/health

# Verificar espacio en disco
df -h
du -sh data/ logs/
```

## 4. Comandos de Mantenimiento

```bash
# Reiniciar contenedor
docker restart <container_name>

# Ver uso de recursos
docker stats <container_name>

# Backup de base de datos (desde host)
docker cp <container_name>:/app/data/mentions.db ./backup_mentions_$(date +%Y%m%d).db

# Restaurar base de datos (desde host)
docker cp ./backup_mentions.db <container_name>:/app/data/mentions.db
```

## 5. Solución de Problemas Comunes

### Base de Datos Corrupta
```bash
# Dentro del contenedor
cd /app
sqlite3 data/mentions.db ".recover" > backup.sql
rm data/mentions.db
sqlite3 data/mentions.db < backup.sql
```

### Reiniciar Servicios
```bash
# Desde el host
docker restart <container_name>

# O si usas docker-compose
docker-compose restart
```

### Limpiar Logs
```bash
# Dentro del contenedor
echo "" > logs/app.log
echo "" > logs/error.log
```

## 6. Monitoreo de Efectividad

```bash
# Dentro del contenedor
# Ver menciones de Andres de Leo (últimas 24h)
sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits WHERE keyword='Andres de Leo' AND created_at > datetime('now', '-1 day');"

# Ver todas las menciones por keyword
sqlite3 data/mentions.db "SELECT keyword, COUNT(*) as total FROM hits GROUP BY keyword ORDER BY total DESC;"

# Ver menciones recientes
sqlite3 data/mentions.db "SELECT keyword, title, url, created_at FROM hits ORDER BY created_at DESC LIMIT 10;"

# Calcular efectividad (menciones únicas vs total)
sqlite3 data/mentions.db "SELECT COUNT(DISTINCT url) as unicas, COUNT(*) as total FROM hits;"
```

## 7. Variables de Entorno Actuales

Tus variables configuradas:
```
TELEGRAM_BOT_TOKEN=8433040986:AAHvugen7amF6vwd8cbTB4NOaNVSqEPelnw
TELEGRAM_CHAT_ID=1880232778
LOG_LEVEL=INFO
SQLITE_PATH=data/mentions.db
TZ=America/Argentina/Buenos_Aires
```

## 8. Comandos de Verificación Rápida

```bash
# Script de verificación completa (ejecutar dentro del contenedor)
echo "=== VERIFICACIÓN RÁPIDA ==="
echo "Contenedor: $(hostname)"
echo "Fecha: $(date)"
echo "Variables: $(env | grep -c -E 'TELEGRAM|LOG|SQLITE|TZ') configuradas"
echo "Base de datos: $(ls -lh data/mentions.db 2>/dev/null || echo 'NO ENCONTRADA')"
echo "Logs: $(ls -lh logs/ 2>/dev/null | wc -l) archivos"
echo "Procesos Python: $(ps aux | grep -c python)"
echo "Salud: $(curl -s http://localhost:5000/health || echo 'ERROR')"
echo "Menciones totales: $(sqlite3 data/mentions.db 'SELECT COUNT(*) FROM hits;' 2>/dev/null || echo 'ERROR')"
echo "Última mención: $(sqlite3 data/mentions.db 'SELECT created_at FROM hits ORDER BY created_at DESC LIMIT 1;' 2>/dev/null || echo 'NINGUNA')"
```

## Notas Importantes

- Reemplaza `<container_name>` con el nombre real de tu contenedor
- En EasyPanel, el nombre del contenedor suele ser el nombre del servicio
- Algunos comandos requieren permisos de administrador
- Siempre haz backup antes de modificar la base de datos
- La efectividad del 82% indica que el sistema está funcionando bien