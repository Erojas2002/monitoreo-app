# monitoreo_app/views.py
from rest_framework import viewsets
from .models import NetworkNode, VirtualHost, Container, LatencyLog, AlertEvent, HTTPEndpoint, HTTPLog
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import (
    NetworkNodeSerializer, 
    VirtualHostSerializer, 
    ContainerSerializer, 
    LatencyLogSerializer, 
    AlertEventSerializer,
    HTTPEndpointSerializer,
    HTTPLogSerializer
)
from .services.report_service import generate_nodes_report_pdf, generate_excel_report
from django.http import FileResponse
from django.db.models import Avg, Count, Min, Max
from datetime import timedelta
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .services.prediction_service import predict_node_failures, get_node_health_score

class NetworkNodeViewSet(viewsets.ModelViewSet):
    queryset = NetworkNode.objects.all()
    serializer_class = NetworkNodeSerializer

    #Endpoint personalizado para las gráficas
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        nodo = self.get_object()
        # Obtenemos los últimos 60 registros (ej. 1 hora si el ping es por minuto)
        logs = nodo.latency_logs.all().order_by('-timestamp')[:60]
        serializer = LatencyLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Obtiene métricas avanzadas de un nodo"""
        nodo = self.get_object()
        days = int(request.GET.get('days', 7))
        
        start_date = timezone.now() - timedelta(days=days)
        logs = nodo.latency_logs.filter(timestamp__gte=start_date)
        
        if not logs.exists():
            return Response({
                'status': 'No hay datos',
                'uptime': 0,
                'avg_latency': 0,
                'max_latency': 0,
                'total_checks': 0
            })
        
        total_checks = logs.count()
        online_checks = logs.filter(is_online=True).count()
        uptime = (online_checks / total_checks * 100) if total_checks > 0 else 0
        
        metrics = {
            'uptime': round(uptime, 2),
            'avg_latency': logs.filter(latency_ms__isnull=False).aggregate(Avg('latency_ms'))['latency_ms__avg'] or 0,
            'max_latency': logs.filter(latency_ms__isnull=False).aggregate(Max('latency_ms'))['latency_ms__max'] or 0,
            'min_latency': logs.filter(latency_ms__isnull=False).aggregate(Min('latency_ms'))['latency_ms__min'] or 0,
            'total_checks': total_checks,
            'online_checks': online_checks,
            'offline_checks': total_checks - online_checks,
            'avg_packet_loss': logs.aggregate(Avg('packet_loss_pct'))['packet_loss_pct__avg'] or 0,
        }
        
        return Response(metrics)

    @action(detail=False, methods=['get'])
    def predictions(self, request):
        """Obtiene predicciones de fallos"""
        predictions = predict_node_failures()
        return Response(predictions)
    
    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """Obtiene el score de salud de un nodo"""
        node = self.get_object()
        score = get_node_health_score(node)
        return Response({
            'node': node.name,
            'health_score': score,
            'status': 'healthy' if score >= 70 else 'warning' if score >= 40 else 'critical'
        })

class VirtualHostViewSet(viewsets.ModelViewSet):
    queryset = VirtualHost.objects.all()
    serializer_class = VirtualHostSerializer

class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all()
    serializer_class = ContainerSerializer

class LatencyLogViewSet(viewsets.ReadOnlyModelViewSet):
    # Usamos ReadOnly porque el frontend solo debe leer los logs, no crearlos ni editarlos
    queryset = LatencyLog.objects.all()
    serializer_class = LatencyLogSerializer

class AlertEventViewSet(viewsets.ModelViewSet):
    queryset = AlertEvent.objects.all()
    serializer_class = AlertEventSerializer
    
    @action(detail=False, methods=['get'])
    def filter(self, request):
        """Filtra alertas por tipo, fecha y estado con paginación"""
        queryset = AlertEvent.objects.all()
        
        # Filtrar por tipo
        event_type = request.GET.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filtrar por estado
        is_resolved = request.GET.get('resolved')
        if is_resolved is not None:
            if is_resolved.lower() == 'true':
                queryset = queryset.filter(is_resolved=True)
            elif is_resolved.lower() == 'false':
                queryset = queryset.filter(is_resolved=False)
        
        # Filtrar por fecha
        date_from = request.GET.get('from')
        if date_from:
            try:
                from_date = timezone.datetime.fromisoformat(date_from)
                queryset = queryset.filter(created_at__gte=from_date)
            except ValueError:
                from_date = timezone.datetime.strptime(date_from, '%Y-%m-%d')
                from_date = timezone.make_aware(from_date)
                queryset = queryset.filter(created_at__gte=from_date)
        
        date_to = request.GET.get('to')
        if date_to:
            try:
                to_date = timezone.datetime.fromisoformat(date_to)
                queryset = queryset.filter(created_at__lte=to_date)
            except ValueError:
                to_date = timezone.datetime.strptime(date_to, '%Y-%m-%d')
                to_date = timezone.make_aware(to_date) + timedelta(days=1) - timedelta(seconds=1)
                queryset = queryset.filter(created_at__lte=to_date)
        
        # Ordenar por fecha descendente
        queryset = queryset.order_by('-created_at')
        
        # Paginación con offset/limit
        total_count = queryset.count()
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        queryset = queryset[offset:offset + limit]
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': total_count,
            'results': serializer.data,
            'next': offset + limit if offset + limit < total_count else None,
            'previous': offset - limit if offset > 0 else None,
        })

    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de alertas"""
        total = AlertEvent.objects.count()
        resolved = AlertEvent.objects.filter(is_resolved=True).count()
        pending = AlertEvent.objects.filter(is_resolved=False).count()
        
        # Alertas por tipo
        types = AlertEvent.objects.values('event_type').annotate(
            count=Count('event_type')
        ).order_by('-count')
        
        # Alertas por día (últimos 7 días)
        daily = []
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = AlertEvent.objects.filter(
                created_at__date=date
            ).count()
            daily.append({
                'date': date.strftime('%d/%m/%Y'),
                'count': count
            })
        
        return Response({
            'total': total,
            'resolved': resolved,
            'pending': pending,
            'resolution_rate': round((resolved / total * 100) if total > 0 else 0, 2),
            'by_type': types,
            'daily': daily
        })

class HTTPEndpointViewSet(viewsets.ModelViewSet):
    queryset = HTTPEndpoint.objects.all()
    serializer_class = HTTPEndpointSerializer

class ReportViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def pdf(self, request):
        buffer = generate_nodes_report_pdf()
        return FileResponse(buffer, as_attachment=True, filename='reporte_monitoreo.pdf')
    
    @action(detail=False, methods=['get'])
    def excel(self, request):
        buffer = generate_excel_report()
        return FileResponse(buffer, as_attachment=True, filename='reporte_monitoreo.xlsx')