from django.contrib import admin
from .models import NetworkNode, VirtualHost, Container, LatencyLog, AlertEvent

@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'device_type', 'status', 'is_monitored')
    list_filter = ('status', 'device_type', 'is_monitored')
    search_fields = ('name', 'ip_address')

@admin.register(LatencyLog)
class LatencyLogAdmin(admin.ModelAdmin):
    list_display = ('node', 'timestamp', 'latency_ms', 'is_online')
    list_filter = ('is_online', 'node')
    date_hierarchy = 'timestamp'
    
@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'node', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'event_type')

# Registros básicos para el resto
admin.site.register(VirtualHost)
admin.site.register(Container)