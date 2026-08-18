# monitoreo_app/services/telegram_service.py
import asyncio
import logging
from typing import Optional
from telegram import Bot, error
from django.conf import settings

logger = logging.getLogger(__name__)

# Variable global para la instancia
_telegram_notifier = None

class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id
        self.bot = None
        self.enabled = False
        
        if self.token and self.chat_id:
            self.bot = Bot(token=self.token)
            self.enabled = True
    
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Envía un mensaje asíncrono a Telegram"""
        if not self.enabled:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"Mensaje Telegram enviado: {message[:50]}...")
            return True
        except error.TelegramError as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False
    
    async def send_alert(self, title: str, message: str, severity: str = 'info') -> bool:
        """Envía una alerta formateada a Telegram"""
        emojis = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }
        
        emoji = emojis.get(severity, 'ℹ️')
        formatted_message = f"""
{emoji} <b>{title}</b>
📋 {message}
        """
        
        return await self.send_message(formatted_message.strip())
    
    def send_sync(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Versión síncrona para usar en el código existente"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.send_message(message, parse_mode))
        except Exception as e:
            logger.error(f"Error en send_sync: {e}")
            return False
    
    def send_alert_sync(self, title: str, message: str, severity: str = 'info') -> bool:
        """Versión síncrona de send_alert"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.send_alert(title, message, severity))
        except Exception as e:
            logger.error(f"Error en send_alert_sync: {e}")
            return False

def get_telegram_notifier():
    """Obtiene o crea la instancia del notificador con la configuración actual"""
    global _telegram_notifier
    
    try:
        from monitoreo_app.models import AppSettings
        settings_obj = AppSettings.objects.first()
        if settings_obj and settings_obj.telegram_bot_token and settings_obj.telegram_chat_id:
            _telegram_notifier = TelegramNotifier(
                token=settings_obj.telegram_bot_token,
                chat_id=settings_obj.telegram_chat_id
            )
            return _telegram_notifier
    except:
        pass
    
    # Fallback a variables de entorno
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    _telegram_notifier = TelegramNotifier(token=token, chat_id=chat_id)
    return _telegram_notifier

# Para mantener compatibilidad con código existente
telegram_notifier = get_telegram_notifier()