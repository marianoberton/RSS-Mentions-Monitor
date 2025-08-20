#!/bin/bash

# Script de deployment para EasyPanel
# Ejecutar este script en tu VPS después de subir los archivos

echo "🚀 Iniciando deployment en EasyPanel..."

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data logs

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado. Creando desde ejemplo..."
    cp .env.example .env
    echo "✏️  IMPORTANTE: Edita el archivo .env con tus tokens de Telegram"
    echo "   - TELEGRAM_BOT_TOKEN=tu_token_aqui"
    echo "   - TELEGRAM_CHAT_ID=tu_chat_id_aqui"
fi

# Verificar permisos del script start.sh
echo "🔧 Configurando permisos..."
chmod +x start.sh

# Mostrar información de deployment
echo ""
echo "📋 INFORMACIÓN DE DEPLOYMENT:"
echo "   - Puerto: 5000"
echo "   - Archivo de configuración: easypanel-deploy.yml"
echo "   - Logs: ./logs/app.log"
echo "   - Base de datos: ./data/mentions.db"
echo ""
echo "🎯 PASOS PARA EASYPANEL:"
echo "   1. Crear nueva aplicación en EasyPanel"
echo "   2. Tipo: Docker Compose"
echo "   3. Subir archivo: easypanel-deploy.yml"
echo "   4. Configurar variables de entorno:"
echo "      - TELEGRAM_BOT_TOKEN=tu_token"
echo "      - TELEGRAM_CHAT_ID=tu_chat_id"
echo "      - FLASK_SECRET_KEY=clave_secreta_aleatoria"
echo "   5. Puerto: 5000"
echo "   6. Dominio: tu-dominio.com"
echo ""
echo "✅ Deployment configurado. Listo para EasyPanel!"

# Opcional: Comprimir archivos para subida
echo "📦 ¿Crear archivo comprimido para subida? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📦 Creando archivo comprimido..."
    tar -czf rss-monitor-deploy.tar.gz \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='.pytest_cache' \
        --exclude='*.pyc' \
        --exclude='.git' \
        .
    echo "✅ Archivo creado: rss-monitor-deploy.tar.gz"
    echo "📤 Sube este archivo a tu VPS y extráelo con:"
    echo "   tar -xzf rss-monitor-deploy.tar.gz"
fi

echo ""
echo "🎉 ¡Deployment listo para EasyPanel!"