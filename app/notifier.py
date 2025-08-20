import requests
import logging
from typing import Dict, Any, List

from app.config import config
from app.utils import escape_html, get_utc_now, format_date

logger = logging.getLogger(__name__)

def send_telegram_notification(hit_details: Dict[str, Any]):
    """Sends a formatted notification to Telegram."""
    token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    
    message = (
        f"📰 <b>{escape_html(hit_details['site'])}</b>\n"
        f"<b>{escape_html(hit_details['title'])}</b>\n"
        f"{hit_details['link']}\n"
        f"🔎 Mención: <i>{escape_html(hit_details['keyword'])}</i> (en {hit_details['where_found']})\n"
        f"🕒 {hit_details['published_local']} (UTC {hit_details['published_utc']})"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Notification sent for article: {hit_details['title']}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {e}")

def send_hourly_summary(stats: Dict[str, Any]):
    """Envía un resumen horario con estadísticas a Telegram."""
    token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    
    now_utc = get_utc_now()
    local_time = format_date(now_utc, config["TZ"])
    
    message = (
        f"⏰ <b>RESUMEN HORARIO - {local_time}</b>\n\n"
        f"📊 <b>Estadísticas:</b>\n"
        f"• Artículos procesados: {stats['total_articles']}\n"
        f"• Tasa de éxito: {stats['success_rate']:.1f}%\n\n"
        f"🔍 <b>Menciones:</b>\n"
        f"• Javier Milei: {stats['milei_mentions']}\n"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("Hourly summary sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send hourly summary: {e}")

def send_important_hits_notifications(important_hits: Dict[str, List[Dict[str, Any]]]):
    """Envía notificaciones específicas para menciones de Liberman y Coria."""
    from app.utils import format_date, get_utc_now
    from app.storage import mark_notification_sent
    from datetime import datetime
    
    token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    
    # Procesar menciones de Liberman
    for hit in important_hits["liberman"]:
        # Formatear fecha de publicación
        try:
            if hit['published_utc']:
                # Manejar diferentes formatos de fecha
                pub_str = hit['published_utc']
                if 'GMT' in pub_str:
                    # Formato RFC 2822 (ej: Wed, 23 Jul 2025 01:06:36 GMT)
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_str)
                else:
                    # Formato ISO
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                formatted_date = pub_date.strftime('%d/%m/%Y %H:%M')
            else:
                formatted_date = "Fecha no disponible"
        except Exception as e:
            formatted_date = str(hit['published_utc']) if hit.get('published_utc') else "Fecha no disponible"
        
        message = (
            f"📢 <b>MENCIÓN IMPORTANTE</b>\n\n"
            f"👤 <b>OSCAR LIBERMAN</b>\n\n"
            f"📰 <b>{escape_html(hit['site'].upper())}</b>\n"
            f"📄 <b>{escape_html(hit['title'])}</b>\n\n"
            f"🔗 <a href=\"{hit['link']}\">Leer artículo completo</a>\n\n"
            f"📅 {formatted_date} UTC\n"
            f"🔍 Detectado en: {hit['where_found']}"
        )
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "disable_notification": False
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Notificación importante enviada para Liberman: {hit['title']}")
            # Marcar como enviada para evitar duplicados
            mark_notification_sent(hit['id'])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar notificación importante de Liberman: {e}")
    
    # Procesar menciones de Coria
    for hit in important_hits["coria"]:
        # Formatear fecha de publicación
        try:
            if hit['published_utc']:
                # Manejar diferentes formatos de fecha
                pub_str = hit['published_utc']
                if 'GMT' in pub_str:
                    # Formato RFC 2822 (ej: Wed, 23 Jul 2025 01:06:36 GMT)
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_str)
                else:
                    # Formato ISO
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                formatted_date = pub_date.strftime('%d/%m/%Y %H:%M')
            else:
                formatted_date = "Fecha no disponible"
        except Exception as e:
            formatted_date = str(hit['published_utc']) if hit.get('published_utc') else "Fecha no disponible"
        
        message = (
            f"📢 <b>MENCIÓN IMPORTANTE</b>\n\n"
            f"👤 <b>GUSTAVO CORIA</b>\n\n"
            f"📰 <b>{escape_html(hit['site'].upper())}</b>\n"
            f"📄 <b>{escape_html(hit['title'])}</b>\n\n"
            f"🔗 <a href=\"{hit['link']}\">Leer artículo completo</a>\n\n"
            f"📅 {formatted_date} UTC\n"
            f"🔍 Detectado en: {hit['where_found']}"
        )
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "disable_notification": False
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Notificación importante enviada para Coria: {hit['title']}")
            # Marcar como enviada para evitar duplicados
            mark_notification_sent(hit['id'])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar notificación importante de Coria: {e}")
    
    # Procesar menciones de Andres de Leo
    for hit in important_hits["andres_de_leo"]:
        # Formatear fecha de publicación
        try:
            if hit['published_utc']:
                # Manejar diferentes formatos de fecha
                pub_str = hit['published_utc']
                if 'GMT' in pub_str:
                    # Formato RFC 2822 (ej: Wed, 23 Jul 2025 01:06:36 GMT)
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_str)
                else:
                    # Formato ISO
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                formatted_date = pub_date.strftime('%d/%m/%Y %H:%M')
            else:
                formatted_date = "Fecha no disponible"
        except Exception as e:
            formatted_date = str(hit['published_utc']) if hit.get('published_utc') else "Fecha no disponible"
        
        message = (
            f"📢 <b>MENCIÓN IMPORTANTE</b>\n\n"
            f"👤 <b>ANDRES DE LEO</b>\n\n"
            f"📰 <b>{escape_html(hit['site'].upper())}</b>\n"
            f"📄 <b>{escape_html(hit['title'])}</b>\n\n"
            f"🔗 <a href=\"{hit['link']}\">Leer artículo completo</a>\n\n"
            f"📅 {formatted_date} UTC\n"
            f"🔍 Detectado en: {hit['where_found']}"
        )
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "disable_notification": False
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Notificación importante enviada para Andres de Leo: {hit['title']}")
            # Marcar como enviada para evitar duplicados
            mark_notification_sent(hit['id'])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar notificación importante de Andres de Leo: {e}")