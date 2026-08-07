# monitoreo_app/services/network_monitor.py
from ping3 import ping
from monitoreo_app.models import NetworkNode, LatencyLog, AlertEvent
from django.utils import timezone
import time
from .telegram_service import telegram_notifier
from django.conf import settings

def check_all_nodes():
    nodos_activos = NetworkNode.objects.filter(is_monitored=True)
    alerts_sent = []

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
            handle_status_change(nodo, nuevo_estado)
            
        nodo.status = nuevo_estado
        nodo.save(update_fields=['status'])

def handle_status_change(nodo, nuevo_estado):
    # Obtener estado anterior
    estado_anterior = nodo.status
    
    if nuevo_estado == 'DOWN':
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) ha dejado de responder."
        AlertEvent.objects.create(node=nodo, event_type='NODE_DOWN', message=mensaje)
        print(f"[ALERTA] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM
        telegram_notifier.send_alert_sync(
            title="🚨 NODO CAÍDO",
            message=f"Dispositivo: <b>{nodo.name}</b>\n"
                    f"IP: <code>{nodo.ip_address}</code>\n"
                    f"Tipo: {nodo.get_device_type_display()}\n\n"
                    f"⚠️ El dispositivo ha dejado de responder al ping.",
            severity="critical"
        )

    elif nuevo_estado == 'UP' and estado_anterior == 'DOWN':
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) está nuevamente en línea."
        alertas_pendientes = AlertEvent.objects.filter(node=nodo, event_type='NODE_DOWN', is_resolved=False)
        for alerta in alertas_pendientes:
            alerta.is_resolved = True
            alerta.resolved_at = timezone.now()
            alerta.save()
        print(f"[RECOVERY] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM
        telegram_notifier.send_alert_sync(
            title="✅ NODO RECUPERADO",
            message=f"Dispositivo: <b>{nodo.name}</b>\n"
                    f"IP: <code>{nodo.ip_address}</code>\n\n"
                    f"El dispositivo está nuevamente en línea.",
            severity="success"
        )
    
    elif nuevo_estado == 'WARN' and estado_anterior != 'WARN':
        mensaje = f"El dispositivo {nodo.name} ({nodo.ip_address}) tiene alta latencia."
        AlertEvent.objects.create(node=nodo, event_type='HIGH_LATENCY', message=mensaje)
        print(f"[ADVERTENCIA] {mensaje}")
        
        # 📱 NOTIFICACIÓN TELEGRAM (solo si está configurado)
        if getattr(settings, 'NOTIFY_ON_WARN', True):
            telegram_notifier.send_alert_sync(
                title="⚠️ LATENCIA ALTA",
                message=f"Dispositivo: <b>{nodo.name}</b>\n"
                        f"IP: <code>{nodo.ip_address}</code>\n"
                        f"Pérdida: {nodo.latency_logs.first().packet_loss_pct:.1f}%\n\n"
                        f"El dispositivo está respondiendo pero con alta latencia.",
                severity="warning"
            )