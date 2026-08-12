# monitoreo_app/serializers.py
from rest_framework import serializers
from .models import NetworkNode, VirtualHost, Container, LatencyLog, AlertEvent, HTTPEndpoint, HTTPLog

class LatencyLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LatencyLog
        fields = [
            'id', 'timestamp', 'latency_ms', 'packet_loss_pct', 'is_online'
        ]

class AlertEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertEvent
        fields = '__all__'

class ContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = '__all__'

class VirtualHostSerializer(serializers.ModelSerializer):
    containers = ContainerSerializer(many=True, read_only=True)
    
    class Meta:
        model = VirtualHost
        fields = ['id', 'name', 'host_type', 'api_endpoint', 'containers']

class NetworkNodeSerializer(serializers.ModelSerializer):
    recent_latency = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkNode
        fields = [
            'id', 'name', 'ip_address', 'device_type', 'status', 
            'is_monitored', 'notify_telegram','recent_latency'
        ]
        # is_monitored siempre será true al crear
        extra_kwargs = {
            'is_monitored': {'default': True},
        }

    def get_recent_latency(self, obj):
        logs = obj.latency_logs.all().order_by('-timestamp')[:10]
        return LatencyLogSerializer(logs, many=True).data


# ============================================
# NUEVOS SERIALIZERS PARA HTTP
# ============================================

class HTTPLogSerializer(serializers.ModelSerializer):
    """Serializer para los logs de endpoints HTTP"""
    
    class Meta:
        model = HTTPLog
        fields = [
            'id', 
            'timestamp', 
            'status_code', 
            'response_time', 
            'is_online', 
            'error_message', 
            'ssl_valid'
        ]


class HTTPEndpointSerializer(serializers.ModelSerializer):
    recent_logs = serializers.SerializerMethodField()
    status_code = serializers.SerializerMethodField()
    last_status_code = serializers.SerializerMethodField()
    service_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = HTTPEndpoint
        fields = [
            'id', 'name', 'url', 'service_type', 'service_type_display',
            'expected_status', 'timeout', 'check_ssl', 'status', 
            'last_response_time', 'ssl_expiry_date',
            'is_active', 'notify_telegram', 'created_at', 'updated_at',
            'recent_logs', 'status_code', 'last_status_code'
        ]
        read_only_fields = [
            'status', 'last_response_time', 'ssl_expiry_date',
            'created_at', 'updated_at'
        ]
    
    def get_recent_logs(self, obj):
        logs = obj.logs.all().order_by('-timestamp')[:10]
        return HTTPLogSerializer(logs, many=True).data
    
    def get_status_code(self, obj):
        last_log = obj.logs.first()
        return last_log.status_code if last_log else None
    
    def get_last_status_code(self, obj):
        return self.get_status_code(obj)
    
    def get_service_type_display(self, obj):
        return obj.get_service_type_display()