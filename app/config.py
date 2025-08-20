import os
import yaml
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

def load_config() -> Dict[str, Any]:
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    config["TELEGRAM_BOT_TOKEN"] = os.getenv("TELEGRAM_BOT_TOKEN")
    config["TELEGRAM_CHAT_ID"] = os.getenv("TELEGRAM_CHAT_ID")
    config["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
    config["SQLITE_PATH"] = os.getenv("SQLITE_PATH", "data/mentions.db")
    config["TZ"] = os.getenv("TZ", "America/Argentina/Buenos_Aires")
    return config

config = load_config()