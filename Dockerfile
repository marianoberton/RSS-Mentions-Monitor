# Imagen oficial Playwright con browsers y deps listas
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# Utilidades (como tenías)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash gcc \
  && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la app
COPY . .

# 👇 Asegurá que exista /start.sh y /app/start.sh, normalizá EOL y permisos
COPY start.sh /start.sh
RUN sed -i 's/\r$//' /app/start.sh && sed -i 's/\r$//' /start.sh \
 && chmod +x /app/start.sh /start.sh

# Directorios persistentes
RUN mkdir -p /app/data /app/logs

# Vars
ENV TZ=America/Argentina/Buenos_Aires \
    FLASK_APP=web_app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# Tu compose llama: ["/start.sh","web"]
CMD ["/start.sh"]
