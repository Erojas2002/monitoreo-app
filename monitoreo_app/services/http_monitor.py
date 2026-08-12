# monitoreo_app/services/http_monitor.py
import requests
import ssl
import socket
import datetime
from django.utils import timezone
from django.conf import settings
from monitoreo_app.models import HTTPEndpoint, HTTPLog, AlertEvent
from .telegram_service import telegram_notifier

# Códigos HTTP que deben generar alerta
HTTP_ERROR_CODES = [400, 401, 403, 404, 405, 408, 500, 501, 502, 503, 504, 505]
HTTP_SUCCESS_CODES = [200, 201, 202, 203, 204]

def check_ssl_expiry(endpoint):
    """Verifica si el SSL está próximo a expirar y envía alerta"""
    if not endpoint.ssl_expiry_date:
        return
    
    days_left = (endpoint.ssl_expiry_date - timezone.now()).days
    
    # Umbrales de alerta
    if days_left <= 7 and days_left > 0:
        severity = 'critical'
        title = f"🔴 SSL por expirar en {days_left} días"
        message = f"Servicio: <b>{endpoint.name}</b>\nURL: <code>{endpoint.url}</code>\n⚠️ El certificado SSL expira en {days_left} días."
    elif days_left <= 30 and days_left > 7:
        severity = 'warning'
        title = f"🟡 SSL expira en {days_left} días"
        message = f"Servicio: <b>{endpoint.name}</b>\nURL: <code>{endpoint.url}</code>\nℹ️ El certificado SSL expira en {days_left} días."
    else:
        return  # No alertar si faltan más de 30 días
    
    # Evitar spam: solo alertar si no se ha enviado antes
    alert_key = f"ssl_{endpoint.id}"
    last_alert = getattr(check_ssl_expiry, 'last_alerts', {})
    
    if alert_key in last_alert:
        last_time = last_alert[alert_key]
        if (timezone.now() - last_time).days < 1:  # No repetir en menos de 24h
            return
    
    # Guardar última alerta
    if not hasattr(check_ssl_expiry, 'last_alerts'):
        check_ssl_expiry.last_alerts = {}
    check_ssl_expiry.last_alerts[alert_key] = timezone.now()
    
    # Enviar alerta por Telegram
    if endpoint.notify_telegram:
        telegram_notifier.send_alert_sync(
            title=title,
            message=message,
            severity=severity
        )
    
    # Guardar en AlertEvent
    AlertEvent.objects.create(
        node=None,
        event_type='SSL_EXPIRY',
        message=f"SSL de {endpoint.name} expira en {days_left} días"
    )

def check_http_endpoint(endpoint):
    """Verifica un endpoint HTTP/HTTPS"""
    try:
        # Realizar la petición
        start_time = timezone.now()
        response = requests.get(
            endpoint.url,
            timeout=endpoint.timeout,
            verify=endpoint.check_ssl
        )
        end_time = timezone.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000  # ms
        
        # Verificar si el código de estado es el esperado
        is_online = response.status_code == endpoint.expected_status
        
        # Verificar SSL si está habilitado
        ssl_valid = True
        ssl_expiry = None
        if ssl_expiry:
            endpoint.ssl_expiry_date = ssl_expiry
            # Verificar expiración
            check_ssl_expiry(endpoint)
        if endpoint.check_ssl and endpoint.url.startswith('https'):
            ssl_valid, ssl_expiry = check_ssl_certificate(endpoint.url)
        
        # Guardar log
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=response.status_code,
            response_time=response_time,
            is_online=is_online,
            ssl_valid=ssl_valid
        )
        
        # Verificar si el código de estado es un error HTTP
        status_code = response.status_code
        if status_code in HTTP_ERROR_CODES:
            # Es un error HTTP, generar alerta inmediata
            handle_http_error(endpoint, status_code, response_time)
        
        # Actualizar estado del endpoint
        nuevo_estado = 'UP' if is_online else 'DOWN'
        if is_online and response_time > 2000:  # Más de 2 segundos
            nuevo_estado = 'WARN'
        
        # Guardar la fecha/hora del cambio de estado
        if endpoint.status != nuevo_estado:
            # Guardar timestamp del cambio
            if nuevo_estado == 'DOWN':
                endpoint.down_since = timezone.now()
            elif nuevo_estado == 'UP' and endpoint.status == 'DOWN':
                endpoint.recovered_at = timezone.now()
            
            handle_http_status_change(endpoint, nuevo_estado, response_time, status_code)
        
        endpoint.status = nuevo_estado
        endpoint.last_response_time = response_time
        if ssl_expiry:
            endpoint.ssl_expiry_date = ssl_expiry
        endpoint.save()
        
        return is_online, response_time
        
    except requests.exceptions.Timeout:
        error = f"Timeout después de {endpoint.timeout} segundos"
        timestamp = timezone.now()
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=endpoint.timeout * 1000,
            is_online=False,
            error_message=error
        )
        # Guardar timestamp de caída
        if endpoint.status != 'DOWN':
            endpoint.down_since = timestamp
            endpoint.save()
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None
        
    except requests.exceptions.ConnectionError:
        error = "Error de conexión"
        timestamp = timezone.now()
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=0,
            is_online=False,
            error_message=error
        )
        if endpoint.status != 'DOWN':
            endpoint.down_since = timestamp
            endpoint.save()
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None
        
    except Exception as e:
        error = str(e)
        timestamp = timezone.now()
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=0,
            is_online=False,
            error_message=error
        )
        if endpoint.status != 'DOWN':
            endpoint.down_since = timestamp
            endpoint.save()
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None

def handle_http_error(endpoint, status_code, response_time):
    """Maneja códigos de error HTTP específicos"""
    # Verificar si debe notificar por Telegram
    should_notify = getattr(endpoint, 'notify_telegram', True)
    
    error_messages = {
        400: "Solicitud incorrecta (Bad Request)",
        401: "No autorizado (Unauthorized)",
        403: "Prohibido (Forbidden)",
        404: "Página no encontrada (Not Found)",
        405: "Método no permitido (Method Not Allowed)",
        408: "Tiempo de solicitud agotado (Request Timeout)",
        500: "Error interno del servidor (Internal Server Error)",
        501: "No implementado (Not Implemented)",
        502: "Puerta de enlace incorrecta (Bad Gateway)",
        503: "Servicio no disponible (Service Unavailable)",
        504: "Tiempo de puerta de enlace agotado (Gateway Timeout)",
        505: "Versión HTTP no soportada (HTTP Version Not Supported)"
    }
    
    error_desc = error_messages.get(status_code, f"Error HTTP {status_code}")
    
    # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
    if should_notify:
        telegram_notifier.send_alert_sync(
            title=f"🌐 ERROR HTTP {status_code}",
            message=f"Servicio: <b>{endpoint.name}</b>\n"
                    f"URL: <code>{endpoint.url}</code>\n"
                    f"Estado: <b>{status_code} - {error_desc}</b>\n"
                    f"Tiempo respuesta: {response_time:.0f}ms\n\n"
                    f"⚠️ El servicio respondió con un error HTTP.",
            severity="critical"
        )
    else:
        print(f"[INFO] Notificaciones Telegram deshabilitadas para {endpoint.name}")
    
    # Siempre crear evento en la base de datos
    AlertEvent.objects.create(
        node=None,
        event_type=f'HTTP_ERROR_{status_code}',
        message=f"El servicio {endpoint.name} respondió con {status_code}: {error_desc}"
    )

def check_ssl_certificate(url):
    """Verifica el certificado SSL de una URL"""
    try:
        hostname = url.replace('https://', '').split('/')[0]
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expiry_date = datetime.datetime.strptime(
                    cert['notAfter'], '%b %d %H:%M:%S %Y %Z'
                )
                expiry_date = timezone.make_aware(expiry_date)
                return True, expiry_date
    except Exception:
        return False, None

def format_datetime(dt):
    """Formatea fecha/hora con zona horaria local"""
    if not dt:
        return "N/A"
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    local_dt = dt.astimezone(timezone.get_current_timezone())
    return local_dt.strftime('%d/%m/%Y %I:%M:%S %p')

# En handle_http_status_change:
def handle_http_status_change(endpoint, nuevo_estado, response_time=None, error=None, status_code=None):
    estado_anterior = endpoint.status
    current_time = timezone.now()
    
    # Verificar si debe notificar por Telegram
    should_notify = getattr(endpoint, 'notify_telegram', True)
    
    if nuevo_estado == 'DOWN':
        endpoint.down_since = current_time
        endpoint.save(update_fields=['down_since'])
        
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) ha dejado de responder."
        AlertEvent.objects.create(node=None, event_type='HTTP_DOWN', message=mensaje)
        print(f"[ALERTA HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify:
            error_msg = f"\nError: {error}" if error else ""
            telegram_notifier.send_alert_sync(
                title="🌐 SERVICIO CAÍDO",
                message=f"Servicio: <b>{endpoint.name}</b>\n"
                        f"URL: <code>{endpoint.url}</code>\n"
                        f"⏰ Hora caída: <b>{format_datetime(current_time)}</b>\n"
                        f"Error: {error or 'Sin respuesta'}{error_msg}\n\n"
                        f"⚠️ El servicio HTTP no está respondiendo.",
                severity="critical"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {endpoint.name}")
        
    elif nuevo_estado == 'UP' and estado_anterior == 'DOWN':
        down_since = getattr(endpoint, 'down_since', None)
        downtime = ""
        if down_since:
            duration = current_time - down_since
            hours = duration.total_seconds() // 3600
            minutes = (duration.total_seconds() % 3600) // 60
            seconds = duration.total_seconds() % 60
            if hours > 0:
                downtime = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            elif minutes > 0:
                downtime = f"{int(minutes)}m {int(seconds)}s"
            else:
                downtime = f"{int(seconds)}s"
        
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) está nuevamente en línea."
        AlertEvent.objects.create(node=None, event_type='HTTP_RECOVERY', message=mensaje)
        print(f"[RECOVERY HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify:
            status_info = f"Código: {status_code}" if status_code else ""
            telegram_notifier.send_alert_sync(
                title="✅ SERVICIO RECUPERADO",
                message=f"Servicio: <b>{endpoint.name}</b>\n"
                        f"URL: <code>{endpoint.url}</code>\n"
                        f"⏰ Hora recuperación: <b>{format_datetime(current_time)}</b>\n"
                        f"⏱️ Tiempo inactivo: {downtime}\n"
                        f"📊 Tiempo respuesta: {response_time:.0f}ms\n"
                        f"{status_info}\n\n"
                        f"✅ El servicio está nuevamente en línea.",
                severity="success"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {endpoint.name}")
        
        endpoint.down_since = None
        endpoint.save(update_fields=['down_since'])
    
    elif nuevo_estado == 'WARN' and estado_anterior != 'WARN':
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) tiene respuesta lenta ({response_time:.0f}ms)."
        AlertEvent.objects.create(node=None, event_type='HTTP_SLOW', message=mensaje)
        print(f"[ADVERTENCIA HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify:
            telegram_notifier.send_alert_sync(
                title="⚠️ SERVICIO LENTO",
                message=f"Servicio: <b>{endpoint.name}</b>\n"
                        f"URL: <code>{endpoint.url}</code>\n"
                        f"⏰ Hora: {format_datetime(current_time)}\n"
                        f"⏱️ Tiempo respuesta: <b>{response_time:.0f}ms</b>\n\n"
                        f"⚠️ El servicio está respondiendo pero con lentitud.",
                severity="warning"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {endpoint.name}")

def check_all_http_endpoints():
    """Verifica todos los endpoints HTTP activos"""
    endpoints = HTTPEndpoint.objects.filter(is_active=True)
    
    for endpoint in endpoints:
        print(f"[HTTP] Verificando {endpoint.name}...")
        check_http_endpoint(endpoint)