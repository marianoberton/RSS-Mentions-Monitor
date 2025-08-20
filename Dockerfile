FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema (agrego bash)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    bash \
  && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Copio start.sh a /start.sh, normalizo EOL y doy permisos
COPY start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh \
 && sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

# (NECESARIO si tu monitor usa Playwright)
RUN python -m pip install --no-cache-dir playwright && playwright install --with-deps
# (opcional) si vas a usar Playwright:
# RUN python -m pip install --no-cache-dir playwright && playwright install --with-deps

# Vars
ENV TZ=America/Argentina/Buenos_Aires \
    FLASK_APP=web_app.py \
    FLASK_ENV=production \
    PYTHONPATH=/app

EXPOSE 5000

# Dejo un CMD por defecto (sirve para pruebas) 
CMD ["/start.sh"]
