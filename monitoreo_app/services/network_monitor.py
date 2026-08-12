# monitoreo_app/services/network_monitor.py
from ping3 import ping
from monitoreo_app.models import NetworkNode, LatencyLog, AlertEvent
from django.utils import timezone
from django.conf import settings
import time
from .telegram_service import telegram_notifier

def check_all_nodes():
    nodos_activos = NetworkNode.objects.filter(is_monitored=True)

    for nodo in nodos_activos:
        print(f"\n[Monitoreo] Procesando {nodo.name} ({nodo.ip_address})...")
        
        pings_exitosos = 0
        total_pings = 3
        latencia_acumulada = 0

        for _ in range(total_pings):
            delay = ping(nodo.ip_address, timeout=1)
            if delay is not None and delay is not False:
                pings_exitosos += 1
                latencia_acumulada += delay
            time.sleep(0.1)

        if pings_exitosos > 0:
            is_online = True
            latency_ms = round((latencia_acumulada / pings_exitosos) * 1000, 2)
            packet_loss = ((total_pings - pings_exitosos) / total_pings) * 100
        else:
            is_online = False
            latency_ms = None
            packet_loss = 100.0

        # GUARDAR RESULTADOS
        LatencyLog.objects.create(
            node=nodo,
            latency_ms=latency_ms,
            packet_loss_pct=packet_loss,
            is_online=is_online
        )

        # ACTUALIZAR ESTADO
        nuevo_estado = 'UP' if is_online else 'DOWN'
        if packet_loss > 0 and is_online and packet_loss < 50:
            nuevo_estado = 'WARN'
        elif packet_loss >= 50 and is_online:
            nuevo_estado = 'DOWN'
        
        if nodo.status != nuevo_estado:
            # Guardar timestamp del cambio
            current_time = timezone.now()
            if nuevo_estado == 'DOWN':
                nodo.down_since = current_time
            elif nuevo_estado == 'UP' and nodo.status == 'DOWN':
                nodo.recovered_at = current_time
            
            handle_status_change(nodo, nuevo_estado)
            
        nodo.status = nuevo_estado
        nodo.save(update_fields=['status'])

def format_datetime(dt):
    """Formatea fecha/hora con zona horaria local"""
    if not dt:
        return "N/A"
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    local_dt = dt.astimezone(timezone.get_current_timezone())
    return local_dt.strftime('%d/%m/%Y %I:%M:%S %p')

def handle_status_change(nodo, nuevo_estado):
    estado_anterior = nodo.status
    current_time = timezone.now()
    
    # Verificar si debe notificar por Telegram
    should_notify = getattr(nodo, 'notify_telegram', True)
    
    if nuevo_estado == 'DOWN':
        nodo.down_since = current_time
        nodo.save(update_fields=['down_since'])
        
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) ha dejado de responder."
        AlertEvent.objects.create(node=nodo, event_type='NODE_DOWN', message=mensaje)
        print(f"[ALERTA] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify and getattr(settings, 'ALERT_SETTINGS', {}).get('NOTIFY_ON_DOWN', True):
            telegram_notifier.send_alert_sync(
                title="🚨 NODO CAÍDO",
                message=f"Dispositivo: <b>{nodo.name}</b>\n"
                        f"IP: <code>{nodo.ip_address}</code>\n"
                        f"Tipo: {nodo.get_device_type_display()}\n"
                        f"⏰ Hora caída: <b>{format_datetime(current_time)}</b>\n\n"
                        f"⚠️ El dispositivo ha dejado de responder al ping.",
                severity="critical"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {nodo.name}")

    elif nuevo_estado == 'UP' and estado_anterior == 'DOWN':
        down_since = getattr(nodo, 'down_since', None)
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
        
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) está nuevamente en línea."
        alertas_pendientes = AlertEvent.objects.filter(node=nodo, event_type='NODE_DOWN', is_resolved=False)
        for alerta in alertas_pendientes:
            alerta.is_resolved = True
            alerta.resolved_at = timezone.now()
            alerta.save()
        print(f"[RECOVERY] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify and getattr(settings, 'ALERT_SETTINGS', {}).get('NOTIFY_ON_RECOVERY', True):
            telegram_notifier.send_alert_sync(
                title="✅ NODO RECUPERADO",
                message=f"Dispositivo: <b>{nodo.name}</b>\n"
                        f"IP: <code>{nodo.ip_address}</code>\n"
                        f"⏰ Hora recuperación: <b>{format_datetime(current_time)}</b>\n"
                        f"⏱️ Tiempo inactivo: {downtime}\n\n"
                        f"✅ El dispositivo está nuevamente en línea.",
                severity="success"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {nodo.name}")
        
        nodo.down_since = None
        nodo.save(update_fields=['down_since'])
    
    elif nuevo_estado == 'WARN' and estado_anterior != 'WARN':
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) tiene alta latencia."
        AlertEvent.objects.create(node=nodo, event_type='HIGH_LATENCY', message=mensaje)
        print(f"[ADVERTENCIA] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (SOLO SI notify_telegram = True)
        if should_notify and getattr(settings, 'ALERT_SETTINGS', {}).get('NOTIFY_ON_WARN', True):
            last_log = nodo.latency_logs.first()
            packet_loss = last_log.packet_loss_pct if last_log else 0
            telegram_notifier.send_alert_sync(
                title="⚠️ LATENCIA ALTA",
                message=f"Dispositivo: <b>{nodo.name}</b>\n"
                        f"IP: <code>{nodo.ip_address}</code>\n"
                        f"⏰ Hora: {format_datetime(current_time)}\n"
                        f"📊 Pérdida: <b>{packet_loss:.1f}%</b>\n\n"
                        f"⚠️ El dispositivo está respondiendo pero con alta latencia.",
                severity="warning"
            )
        else:
            print(f"[INFO] Notificaciones Telegram deshabilitadas para {nodo.name}")