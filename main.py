import logging
import logging.handlers

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
    init_db()
    run_scheduler()