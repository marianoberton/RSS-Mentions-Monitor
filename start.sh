#!/bin/bash

# Script de inicio para ejecutar tanto el monitor RSS como la interfaz web

echo "Iniciando RSS Mentions Monitor con interfaz web..."

# Función para manejar señales de terminación
cleanup() {
    echo "Deteniendo servicios..."
    kill $MONITOR_PID $WEB_PID 2>/dev/null
    wait
    exit 0
}

# Configurar manejo de señales
trap cleanup SIGTERM SIGINT

# Iniciar el monitor RSS en segundo plano
echo "Iniciando monitor RSS..."
python main.py &
MONITOR_PID=$!

# Esperar un poco para que el monitor se inicialice
sleep 5

# Iniciar la interfaz web
echo "Iniciando interfaz web en puerto 5000..."
python -m flask --app web_app run --host=0.0.0.0 --port=5000 &
WEB_PID=$!

echo "Servicios iniciados:"
echo "- Monitor RSS (PID: $MONITOR_PID)"
echo "- Interfaz Web (PID: $WEB_PID)"
echo "- Interfaz web disponible en http://localhost:5000"

# Esperar a que terminen los procesos
wait