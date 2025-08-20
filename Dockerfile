FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para la base de datos
RUN mkdir -p /app/data

# Variables de entorno
ENV TZ=America/Argentina/Buenos_Aires
ENV FLASK_APP=web_app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Exponer puerto para la interfaz web
EXPOSE 5000

# Script de inicio que ejecuta tanto el monitor como la web
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]