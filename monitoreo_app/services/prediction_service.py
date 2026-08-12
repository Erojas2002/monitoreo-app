# monitoreo_app/services/prediction_service.py
from django.utils import timezone
from datetime import timedelta
from monitoreo_app.models import NetworkNode, LatencyLog, AlertEvent
from django.db.models import Avg  # <-- CAMBIAR: importar solo Avg
import statistics

def predict_node_failures():
    """Predice posibles fallos basado en patrones históricos"""
    predictions = []
    nodes = NetworkNode.objects.filter(is_monitored=True)
    
    for node in nodes:
        # Obtener logs de los últimos 7 días
        start_date = timezone.now() - timedelta(days=7)
        logs = node.latency_logs.filter(timestamp__gte=start_date).order_by('timestamp')
        
        if logs.count() < 10:
            continue
        
        # Calcular métricas de estabilidad
        latencies = [log.latency_ms for log in logs if log.latency_ms]
        if not latencies:
            continue
        
        # 1. Detectar incremento gradual de latencia
        if len(latencies) > 5:
            first_half = statistics.mean(latencies[:len(latencies)//2])
            second_half = statistics.mean(latencies[len(latencies)//2:])
            if second_half > first_half * 1.5:  # 50% de incremento
                predictions.append({
                    'node': {
                        'id': node.id,
                        'name': node.name,
                        'ip_address': node.ip_address,
                        'device_type': node.device_type,
                    },
                    'type': 'latency_trend',
                    'severity': 'warning',
                    'message': f"La latencia ha aumentado un {((second_half/first_half)-1)*100:.0f}% en los últimos días",
                    'detail': f"Promedio inicial: {first_half:.1f}ms, Actual: {second_half:.1f}ms"
                })
        
        # 2. Detectar caídas frecuentes
        recent_week = timezone.now() - timedelta(days=7)
        down_events = AlertEvent.objects.filter(
            node=node,
            event_type='NODE_DOWN',
            created_at__gte=recent_week
        ).count()
        
        if down_events >= 3:
            predictions.append({
                'node': {
                    'id': node.id,
                    'name': node.name,
                    'ip_address': node.ip_address,
                    'device_type': node.device_type,
                },
                'type': 'frequent_downtime',
                'severity': 'critical',
                'message': f"El nodo ha tenido {down_events} caídas en la última semana",
                'detail': "Posible problema de hardware o red"
            })
        
        # 3. Detectar pérdida de paquetes alta
        packet_losses = [log.packet_loss_pct for log in logs if log.packet_loss_pct > 0]
        if packet_losses:
            avg_loss = statistics.mean(packet_losses)
            if avg_loss > 20:
                predictions.append({
                    'node': {
                        'id': node.id,
                        'name': node.name,
                        'ip_address': node.ip_address,
                        'device_type': node.device_type,
                    },
                    'type': 'high_packet_loss',
                    'severity': 'warning',
                    'message': f"Alta pérdida de paquetes ({avg_loss:.1f}% promedio)",
                    'detail': "Revisar conexión de red o cables"
                })
        
        # 4. Detectar patrones de caída (ej: siempre a la misma hora)
        if down_events > 0:
            down_times = AlertEvent.objects.filter(
                node=node,
                event_type='NODE_DOWN',
                created_at__gte=recent_week
            ).values_list('created_at', flat=True)
            
            hours = [dt.hour for dt in down_times]
            if hours and len(set(hours)) < len(hours):  # Hay horas repetidas
                most_common_hour = max(set(hours), key=hours.count)
                if hours.count(most_common_hour) >= 2:
                    predictions.append({
                        'node': {
                            'id': node.id,
                            'name': node.name,
                            'ip_address': node.ip_address,
                            'device_type': node.device_type,
                        },
                        'type': 'pattern',
                        'severity': 'info',
                        'message': f"Patrón de caída detectado a las {most_common_hour}:00",
                        'detail': "Posible mantenimiento programado o sobrecarga horaria"
                    })
    
    return predictions

def get_node_health_score(node, days=7):
    """Calcula un score de salud para un nodo (0-100)"""
    start_date = timezone.now() - timedelta(days=days)
    logs = node.latency_logs.filter(timestamp__gte=start_date)
    
    if logs.count() == 0:
        return 50  # Score neutral sin datos
    
    # Factores que afectan el score
    score = 100
    
    # 1. Disponibilidad (máximo 40 puntos)
    online_count = logs.filter(is_online=True).count()
    uptime_pct = (online_count / logs.count()) * 100
    score -= (100 - uptime_pct) * 0.4
    
    # 2. Latencia (máximo 30 puntos)
    latencies = [log.latency_ms for log in logs if log.latency_ms]
    if latencies:
        avg_latency = statistics.mean(latencies)
        if avg_latency > 200:
            score -= min(30, (avg_latency - 200) / 10)
    
    # 3. Pérdida de paquetes (máximo 20 puntos)
    avg_loss = logs.aggregate(Avg('packet_loss_pct'))['packet_loss_pct__avg'] or 0
    score -= avg_loss * 0.5
    
    # 4. Caídas recientes (máximo 10 puntos)
    recent_down = AlertEvent.objects.filter(
        node=node,
        event_type='NODE_DOWN',
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    score -= recent_down * 5
    
    return max(0, min(100, int(score)))