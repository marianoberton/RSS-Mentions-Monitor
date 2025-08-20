# Imagen oficial Playwright con browsers + deps (estable)
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# Utilidades que usabas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash gcc \
  && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Normalizar EOL y permisos del start.sh en ambos paths
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh \
 && sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# Crear carpetas persistentes (si no existen)
RUN mkdir -p /app/data /app/logs

# Variables de entorno
ENV TZ=America/Argentina/Buenos_Aires \
    FLASK_APP=web_app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Arranque por defecto (tu compose llama /start.sh web)
CMD ["/start.sh"]
