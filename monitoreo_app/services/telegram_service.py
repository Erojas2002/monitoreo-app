# monitoreo_app/services/telegram_service.py
# Reemplazar todo el archivo con este contenido completo

import asyncio
import logging
from typing import Optional, List, Dict
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


def get_telegram_notifier() -> TelegramNotifier:
    """Obtiene la instancia del notificador global (configuración de AppSettings)"""
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


def get_all_telegram_notifiers(event_type: str = None) -> List[Dict]:
    """
    Obtiene todos los notificadores configurados (app global + usuarios).
    
    Args:
        event_type: Tipo de evento ('NODE_DOWN', 'NODE_RECOVERY', 'HTTP_DOWN', 
                   'HTTP_RECOVERY', 'SSL_EXPIRY', 'HIGH_LATENCY')
    
    Returns:
        Lista de diccionarios con {'name': str, 'notifier': TelegramNotifier}
    """
    notifiers = []
    
    # 1. Notificador de la app (configuración global)
    try:
        from monitoreo_app.models import AppSettings
        app_settings = AppSettings.objects.first()
        if app_settings and app_settings.telegram_bot_token and app_settings.telegram_chat_id:
            notifiers.append({
                'name': 'App Global',
                'type': 'app',
                'notifier': TelegramNotifier(
                    token=app_settings.telegram_bot_token,
                    chat_id=app_settings.telegram_chat_id
                )
            })
    except Exception as e:
        logger.error(f"Error obteniendo notificador global: {e}")
    
    # 2. Notificadores de usuarios
    try:
        from monitoreo_app.models import UserProfile
        
        profiles = UserProfile.objects.filter(
            is_active=True
        ).exclude(
            telegram_bot_token__isnull=True
        ).exclude(
            telegram_bot_token=''
        ).exclude(
            telegram_chat_id__isnull=True
        ).exclude(
            telegram_chat_id=''
        ).select_related('user')
        
        for profile in profiles:
            # Verificar si el usuario quiere recibir este tipo de evento
            if event_type:
                should_notify = True
                
                if event_type in ['NODE_DOWN']:
                    should_notify = profile.notify_node_down
                elif event_type in ['NODE_RECOVERY']:
                    should_notify = profile.notify_node_recovery
                elif event_type in ['HTTP_DOWN', 'HTTP_ERROR']:
                    should_notify = profile.notify_http_down
                elif event_type in ['HTTP_RECOVERY']:
                    should_notify = profile.notify_http_recovery
                elif event_type in ['SSL_EXPIRY']:
                    should_notify = profile.notify_ssl_expiry
                elif event_type in ['HIGH_LATENCY']:
                    should_notify = profile.notify_high_latency
                
                if not should_notify:
                    continue
            
            notifiers.append({
                'name': profile.user.username,
                'type': 'user',
                'profile': profile,
                'notifier': TelegramNotifier(
                    token=profile.telegram_bot_token,
                    chat_id=profile.telegram_chat_id
                )
            })
    except Exception as e:
        logger.error(f"Error obteniendo notificadores de usuarios: {e}")
    
    return notifiers


def send_alert_to_all(title: str, message: str, severity: str = 'info', event_type: str = None) -> int:
    """
    Envía una alerta a TODOS los notificadores configurados (app + usuarios).
    
    Args:
        title: Título de la alerta
        message: Mensaje de la alerta
        severity: Severidad ('critical', 'warning', 'info', 'success')
        event_type: Tipo de evento para filtrar preferencias de usuarios
    
    Returns:
        Número de notificaciones enviadas exitosamente
    """
    notifiers = get_all_telegram_notifiers(event_type=event_type)
    success_count = 0
    
    for item in notifiers:
        try:
            if item['notifier'].send_alert_sync(title, message, severity):
                success_count += 1
                logger.info(f"Alerta enviada a {item['name']}")
            else:
                logger.warning(f"No se pudo enviar alerta a {item['name']}")
        except Exception as e:
            logger.error(f"Error enviando alerta a {item['name']}: {e}")
    
    return success_count


# Para mantener compatibilidad con código existente
telegram_notifier = get_telegram_notifier()