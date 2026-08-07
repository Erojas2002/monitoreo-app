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

class HTTPEndpointViewSet(viewsets.ModelViewSet):
    queryset = HTTPEndpoint.objects.all()
    serializer_class = HTTPEndpointSerializer