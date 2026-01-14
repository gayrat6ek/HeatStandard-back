import aiohttp
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_message(telegram_id: str, text: str):
    """Send a message to a Telegram user."""
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, skipping message")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to send telegram message: {await response.text()}")
                else:
                    logger.info(f"Message sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Error sending telegram message: {e}")
