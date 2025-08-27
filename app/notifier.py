import requests
import logging
from typing import Dict, Any, List

from app.config import config
from app.utils import escape_html, get_utc_now, format_date
# Las funciones de suscripciones están en add_candidate_subscriptions.py

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
        f"⏰ <b>RESUMEN CADA 6 HORAS - {local_time}</b>\n\n"
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

def send_immediate_important_notification(article: Dict[str, Any], hit: Dict[str, Any]):
    """Envía una notificación inmediata para menciones importantes."""
    from app.utils import format_date
    from app.storage import mark_notification_sent
    from datetime import datetime
    
    token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    
    # Determinar el nombre de la persona mencionada
    keyword_lower = hit['keyword'].lower()
    if 'liberman' in keyword_lower:
        person_name = "OSCAR LIBERMAN"
        emoji = "👤"
    elif 'coria' in keyword_lower:
        person_name = "GUSTAVO CORIA"
        emoji = "👨‍💼"
    elif 'andres de leo' in keyword_lower:
        person_name = "ANDRES DE LEO"
        emoji = "👨‍💻"
    else:
        person_name = hit['keyword'].upper()
        emoji = "👤"
    
    # Formatear fecha de publicación
    try:
        if article.get('published_utc'):
            pub_str = article['published_utc']
            if 'GMT' in pub_str:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(pub_str)
            else:
                pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
            formatted_date = pub_date.strftime('%d/%m/%Y %H:%M')
        else:
            formatted_date = "Fecha no disponible"
    except Exception as e:
        formatted_date = str(article.get('published_utc', 'Fecha no disponible'))
    
    message = (
        f"🚨 <b>NOTIFICACIÓN INMEDIATA</b>\n\n"
        f"{emoji} <b>{person_name}</b>\n\n"
        f"📰 <b>{escape_html(article['site'].upper())}</b>\n"
        f"📄 <b>{escape_html(article['title'])}</b>\n\n"
        f"🔗 <a href=\"{article['link']}\">Leer artículo completo</a>\n\n"
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
        logger.info(f"Notificación inmediata enviada para {person_name}: {article['title']}")
        # Marcar como enviada para evitar duplicados
        mark_notification_sent(hit['id'])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al enviar notificación inmediata para {person_name}: {e}")

# === NUEVAS FUNCIONES PARA SUSCRIPCIONES MÚLTIPLES ===

def send_candidate_notification(candidate_id: int, article: Dict[str, Any], hit: Dict[str, Any], notification_type: str = 'mention'):
    """Envía notificación a todos los suscriptores de un candidato específico."""
    from add_candidate_subscriptions import get_candidate_subscriptions
    from app.storage import get_db_connection
    from datetime import datetime
    
    try:
        # Obtener información del candidato
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT name, political_party, electoral_section
                FROM candidates 
                WHERE id = ? AND is_active = 1
            """, (candidate_id,))
            candidate_info = cursor.fetchone()
            
            if not candidate_info:
                logger.warning(f"Candidato {candidate_id} no encontrado o inactivo")
                return
        
        candidate_name = candidate_info[0]
        political_party = candidate_info[1]
        
        # Obtener suscripciones activas para este candidato
        subscriptions = get_candidate_subscriptions(candidate_id)
        
        if not subscriptions:
            logger.info(f"No hay suscripciones activas para el candidato {candidate_name}")
            return
        
        # Formatear fecha de publicación
        try:
            if article.get('published_utc'):
                pub_str = article['published_utc']
                if 'GMT' in pub_str:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_str)
                else:
                    pub_date = datetime.fromisoformat(pub_str.replace('Z', '+00:00'))
                formatted_date = pub_date.strftime('%d/%m/%Y %H:%M')
            else:
                formatted_date = "Fecha no disponible"
        except Exception as e:
            formatted_date = str(article.get('published_utc', 'Fecha no disponible'))
        
        # Crear mensaje según el tipo de notificación
        if notification_type == 'urgent':
            emoji = "🚨"
            title_prefix = "NOTIFICACIÓN URGENTE"
        elif notification_type == 'digest':
            emoji = "📊"
            title_prefix = "RESUMEN DIARIO"
        else:
            emoji = "📢"
            title_prefix = "NUEVA MENCIÓN"
        
        message = (
            f"{emoji} <b>{title_prefix}</b>\n\n"
            f"👤 <b>{escape_html(candidate_name.upper())}</b>\n"
            f"🏛️ {escape_html(political_party)}\n\n"
            f"📰 <b>{escape_html(article['site'].upper())}</b>\n"
            f"📄 <b>{escape_html(article['title'])}</b>\n\n"
            f"🔗 <a href=\"{article['link']}\">Leer artículo completo</a>\n\n"
            f"📅 {formatted_date} UTC\n"
            f"🔍 Detectado en: {hit['where_found']}\n"
            f"🔎 Palabra clave: <i>{escape_html(hit['keyword'])}</i>"
        )
        
        token = config["TELEGRAM_BOT_TOKEN"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Enviar a cada suscriptor
        sent_count = 0
        for subscription in subscriptions:
            chat_id = subscription[0]
            subscriber_name = subscription[1]
            notification_types = subscription[2]
            
            # Verificar si el suscriptor quiere este tipo de notificación
            if notification_types != 'all' and notification_type != notification_types:
                continue
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
                "disable_notification": notification_type == 'digest'
            }
            
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                sent_count += 1
                logger.info(f"Notificación enviada a {subscriber_name or chat_id} para candidato {candidate_name}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error al enviar notificación a {chat_id}: {e}")
        
        logger.info(f"Notificaciones enviadas: {sent_count}/{len(subscriptions)} para candidato {candidate_name}")
        
        # Marcar la notificación como enviada para evitar duplicados
        if sent_count > 0:
            from app.storage import mark_notification_sent
            mark_notification_sent(hit['id'])
        
    except Exception as e:
        logger.error(f"Error en send_candidate_notification para candidato {candidate_id}: {e}")

def send_candidate_digest(candidate_id: int, mentions_summary: Dict[str, Any]):
    """Envía un resumen diario de menciones a los suscriptores de un candidato."""
    from add_candidate_subscriptions import get_subscriptions_for_candidate
    from app.storage import get_db_connection
    
    try:
        # Obtener información del candidato
        conn = get_db_connection()
        with conn:
            cursor = conn.execute("""
                SELECT name, political_party
                FROM candidates 
                WHERE id = ? AND is_active = 1
            """, (candidate_id,))
            candidate_info = cursor.fetchone()
            
            if not candidate_info:
                logger.warning(f"Candidato {candidate_id} no encontrado o inactivo")
                return
        
        candidate_name = candidate_info[0]
        political_party = candidate_info[1]
        
        # Obtener suscripciones que quieren digests
        subscriptions = get_subscriptions_for_candidate(candidate_id)
        digest_subscribers = [sub for sub in subscriptions if sub[2] in ['all', 'digest']]
        
        if not digest_subscribers:
            logger.info(f"No hay suscriptores de digest para el candidato {candidate_name}")
            return
        
        # Crear mensaje de resumen
        total_mentions = mentions_summary.get('total_mentions', 0)
        top_sites = mentions_summary.get('top_sites', [])
        recent_mentions = mentions_summary.get('recent_mentions', [])
        
        message = (
            f"📊 <b>RESUMEN DIARIO</b>\n\n"
            f"👤 <b>{escape_html(candidate_name.upper())}</b>\n"
            f"🏛️ {escape_html(political_party)}\n\n"
            f"📈 <b>Total de menciones hoy:</b> {total_mentions}\n\n"
        )
        
        if top_sites:
            message += "🏆 <b>Sitios con más menciones:</b>\n"
            for site, count in top_sites[:3]:
                message += f"• {escape_html(site)}: {count} menciones\n"
            message += "\n"
        
        if recent_mentions:
            message += "📰 <b>Menciones recientes:</b>\n"
            for mention in recent_mentions[:3]:
                message += f"• <a href=\"{mention['link']}\">{escape_html(mention['title'][:50])}...</a>\n"
        
        token = config["TELEGRAM_BOT_TOKEN"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Enviar a cada suscriptor de digest
        sent_count = 0
        for subscription in digest_subscribers:
            chat_id = subscription[0]
            subscriber_name = subscription[1]
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "disable_notification": True
            }
            
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                sent_count += 1
                logger.info(f"Digest enviado a {subscriber_name or chat_id} para candidato {candidate_name}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error al enviar digest a {chat_id}: {e}")
        
        logger.info(f"Digests enviados: {sent_count}/{len(digest_subscribers)} para candidato {candidate_name}")
        
    except Exception as e:
        logger.error(f"Error en send_candidate_digest para candidato {candidate_id}: {e}")

def get_candidate_id_by_keyword(keyword: str) -> int:
    """Obtiene el ID del candidato asociado a una palabra clave."""
    from app.storage import get_db_connection
    
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.execute("""
                SELECT c.id, c.name
                FROM candidates c
                JOIN candidate_keywords ck ON c.id = ck.candidate_id
                WHERE ck.keyword = ? AND c.is_active = 1 AND ck.is_active = 1
                LIMIT 1
            """, (keyword,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                logger.warning(f"No se encontró candidato para la palabra clave: {keyword}")
                return None
    finally:
        conn.close()