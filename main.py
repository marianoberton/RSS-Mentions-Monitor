import logging
import logging.handlers
import os

from app.config import config
from app.storage import init_db
from app.scheduler import run_scheduler

# Logging Setup
log_file = "logs/app.log"
logging.basicConfig(
    level=config["LOG_LEVEL"],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    # Ejecutar migraciones automáticamente al inicio
    try:
        from migrate_db import main as run_migrations
        logging.info("Ejecutando migraciones de base de datos...")
        if run_migrations():
            logging.info("Migraciones completadas exitosamente")
        else:
            logging.error("Error en migraciones, continuando con init_db()")
    except Exception as e:
        logging.error(f"Error ejecutando migraciones: {e}, usando init_db() como fallback")
    
    # Inicializar base de datos (fallback si las migraciones fallan)
    init_db()
    
    # Ejecutar scheduler
    run_scheduler()