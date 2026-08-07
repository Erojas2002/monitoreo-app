# monitoreo_app/services/http_monitor.py
import requests
import ssl
import socket
import datetime
from django.utils import timezone
from monitoreo_app.models import HTTPEndpoint, HTTPLog, AlertEvent
from .telegram_service import telegram_notifier

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
        is_online = response.status_code == endpoint.expected_status
        
        # Verificar SSL si está habilitado
        ssl_valid = True
        ssl_expiry = None
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
        
        # Actualizar estado del endpoint
        nuevo_estado = 'UP' if is_online else 'DOWN'
        if is_online and response_time > 2000:  # Más de 2 segundos
            nuevo_estado = 'WARN'
        
        if endpoint.status != nuevo_estado:
            handle_http_status_change(endpoint, nuevo_estado, response_time)
        
        endpoint.status = nuevo_estado
        endpoint.last_response_time = response_time
        if ssl_expiry:
            endpoint.ssl_expiry_date = ssl_expiry
        endpoint.save()
        
        return is_online, response_time
        
    except requests.exceptions.Timeout:
        error = f"Timeout después de {endpoint.timeout} segundos"
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=endpoint.timeout * 1000,
            is_online=False,
            error_message=error
        )
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None
        
    except requests.exceptions.ConnectionError:
        error = "Error de conexión"
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=0,
            is_online=False,
            error_message=error
        )
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None
        
    except Exception as e:
        error = str(e)
        HTTPLog.objects.create(
            endpoint=endpoint,
            status_code=None,
            response_time=0,
            is_online=False,
            error_message=error
        )
        handle_http_status_change(endpoint, 'DOWN', None, error)
        return False, None

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

def handle_http_status_change(endpoint, nuevo_estado, response_time=None, error=None):
    """Maneja cambios de estado en endpoints HTTP"""
    estado_anterior = endpoint.status
    
    if nuevo_estado == 'DOWN':
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) ha dejado de responder."
        AlertEvent.objects.create(
            node=None,
            event_type='HTTP_DOWN',
            message=mensaje
        )
        print(f"[ALERTA HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM
        error_msg = f"\nError: {error}" if error else ""
        telegram_notifier.send_alert_sync(
            title="🌐 SERVICIO CAÍDO",
            message=f"Servicio: <b>{endpoint.name}</b>\n"
                    f"URL: <code>{endpoint.url}</code>\n"
                    f"Error: {error or 'Sin respuesta'}\n\n"
                    f"⚠️ El servicio HTTP no está respondiendo.",
            severity="critical"
        )
        
    elif nuevo_estado == 'UP' and estado_anterior == 'DOWN':
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) está nuevamente en línea."
        AlertEvent.objects.create(
            node=None,
            event_type='HTTP_RECOVERY',
            message=mensaje
        )
        print(f"[RECOVERY HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM
        telegram_notifier.send_alert_sync(
            title="✅ SERVICIO RECUPERADO",
            message=f"Servicio: <b>{endpoint.name}</b>\n"
                    f"URL: <code>{endpoint.url}</code>\n"
                    f"Tiempo de respuesta: {response_time:.0f}ms\n\n"
                    f"El servicio está nuevamente en línea.",
            severity="success"
        )
    
    elif nuevo_estado == 'WARN' and estado_anterior != 'WARN':
        mensaje = f"El servicio {endpoint.name} ({endpoint.url}) tiene respuesta lenta ({response_time:.0f}ms)."
        AlertEvent.objects.create(
            node=None,
            event_type='HTTP_SLOW',
            message=mensaje
        )
        print(f"[ADVERTENCIA HTTP] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM
        telegram_notifier.send_alert_sync(
            title="⚠️ SERVICIO LENTO",
            message=f"Servicio: <b>{endpoint.name}</b>\n"
                    f"URL: <code>{endpoint.url}</code>\n"
                    f"Tiempo de respuesta: {response_time:.0f}ms\n\n"
                    f"El servicio está respondiendo pero con lentitud.",
            severity="warning"
        )

def check_all_http_endpoints():
    """Verifica todos los endpoints HTTP activos"""
    endpoints = HTTPEndpoint.objects.filter(is_active=True)
    
    for endpoint in endpoints:
        print(f"[HTTP] Verificando {endpoint.name}...")
        check_http_endpoint(endpoint)