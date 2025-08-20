#!/bin/bash
# Comandos para ejecutar en la consola Docker de EasyPanel
# Copia y pega estos comandos uno por uno

echo "=== VERIFICACIÓN RÁPIDA DEL SISTEMA ==="

# 1. Verificar variables de entorno
echo "--- Variables de entorno ---"
env | grep -E "TELEGRAM|LOG|SQLITE|TZ"

# 2. Verificar estructura de archivos
echo "--- Estructura de archivos ---"
ls -la
echo "Directorio data:"
ls -la data/ 2>/dev/null || echo "Directorio data no encontrado"
echo "Directorio logs:"
ls -la logs/ 2>/dev/null || echo "Directorio logs no encontrado"

# 3. Verificar base de datos
echo "--- Estado de la base de datos ---"
if [ -f "data/mentions.db" ]; then
    echo "✅ Base de datos encontrada"
    echo "Tamaño: $(ls -lh data/mentions.db | awk '{print $5}')"
    echo "Integridad:"
    sqlite3 data/mentions.db "PRAGMA integrity_check;" 2>/dev/null || echo "❌ Error verificando integridad"
    echo "Total de menciones:"
    sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits;" 2>/dev/null || echo "❌ Error contando menciones"
else
    echo "❌ Base de datos no encontrada"
fi

# 4. Verificar logs recientes
echo "--- Logs recientes ---"
if [ -f "logs/app.log" ]; then
    echo "✅ Log principal encontrado"
    echo "Últimas 3 líneas:"
    tail -n 3 logs/app.log
else
    echo "❌ Log principal no encontrado"
fi

# 5. Verificar procesos
echo "--- Procesos Python ---"
ps aux | grep python | grep -v grep

# 6. Verificar conectividad
echo "--- Conectividad ---"
echo "Salud del servicio:"
curl -s http://localhost:5000/health 2>/dev/null || echo "❌ Servicio no responde"
echo "Conectividad externa:"
curl -I -s https://www.lanacion.com.ar/ | head -1 2>/dev/null || echo "❌ Sin conectividad externa"

# 7. Análisis específico de Andres de Leo
echo "--- Análisis Andres de Leo ---"
if [ -f "data/mentions.db" ]; then
    echo "Menciones totales de Andres de Leo:"
    sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits WHERE keyword='Andres de Leo';" 2>/dev/null || echo "❌ Error consultando"
    echo "Menciones últimas 24h:"
    sqlite3 data/mentions.db "SELECT COUNT(*) FROM hits WHERE keyword='Andres de Leo' AND created_at > datetime('now', '-1 day');" 2>/dev/null || echo "❌ Error consultando"
    echo "Última mención:"
    sqlite3 data/mentions.db "SELECT title, created_at FROM hits WHERE keyword='Andres de Leo' ORDER BY created_at DESC LIMIT 1;" 2>/dev/null || echo "❌ Error consultando"
fi

# 8. Cálculo de efectividad
echo "--- Cálculo de Efectividad ---"
if [ -f "data/mentions.db" ]; then
    echo "URLs únicas vs total:"
    sqlite3 data/mentions.db "SELECT COUNT(DISTINCT url) as unicas, COUNT(*) as total, ROUND((COUNT(DISTINCT url) * 100.0 / COUNT(*)), 1) as efectividad FROM hits;" 2>/dev/null || echo "❌ Error calculando efectividad"
fi

echo "\n=== COMANDOS ADICIONALES ÚTILES ==="
echo "Para ejecutar diagnóstico completo: python diagnostico_vps.py"
echo "Para verificar efectividad: python verificar_efectividad.py"
echo "Para ver logs en tiempo real: tail -f logs/app.log"
echo "Para reiniciar (desde host): docker restart <container_name>"
echo "Para backup de BD: cp data/mentions.db data/backup_\$(date +%Y%m%d).db"