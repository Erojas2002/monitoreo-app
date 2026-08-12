# monitoreo_app/models.py
from django.db import models

class NetworkNode(models.Model):
    DEVICE_TYPES = [
        ('ROUTER', 'Router'),
        ('SWITCH', 'Switch'),
        ('NVR', 'NVR / DVR'),
        ('CAMERA', 'Cámara IP'),
        ('SERVER', 'Servidor Físico'),
        ('OTHER', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('UP', 'En línea'),
        ('DOWN', 'Caído'),
        ('WARN', 'Advertencia (Latencia alta)'),
        ('UNKNOWN', 'Desconocido'),
    ]

    name = models.CharField(max_length=150, verbose_name="Nombre del Dispositivo")
    ip_address = models.GenericIPAddressField(unique=True, verbose_name="Dirección IP")
    mac_address = models.CharField(max_length=17, blank=True, null=True, verbose_name="Dirección MAC")
    
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='OTHER')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNKNOWN')

    down_since = models.DateTimeField(null=True, blank=True, verbose_name="Caído desde")
    recovered_at = models.DateTimeField(null=True, blank=True, verbose_name="Recuperado a las")
    
    # Para monitoreo y escaneo
    is_monitored = models.BooleanField(default=True, help_text="Desmarcar para ignorar en el escaneo automático")

    notify_telegram = models.BooleanField(default=True, help_text="Enviar notificaciones por Telegram")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class VirtualHost(models.Model):
    HOST_TYPES = [
        ('PROXMOX', 'Proxmox VE'),
        ('DOCKER', 'Docker Daemon'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre del Host (Ej. Nodo Proxmox)")
    host_type = models.CharField(max_length=20, choices=HOST_TYPES)
    api_endpoint = models.URLField(help_text="URL de la API (ej. https://192.168.1.100:8006 para Proxmox)")
    api_token = models.CharField(max_length=255, help_text="Token de acceso o credenciales")
    
    node_reference = models.OneToOneField(NetworkNode, on_delete=models.SET_NULL, null=True, blank=True, related_name='virtual_host')

    def __str__(self):
        return self.name


class Container(models.Model):
    STATUS_CHOICES = [
        ('RUNNING', 'En ejecución'),
        ('STOPPED', 'Detenido'),
        ('PAUSED', 'Pausado'),
        ('UNKNOWN', 'Desconocido'),
    ]

    host = models.ForeignKey(VirtualHost, on_delete=models.CASCADE, related_name='containers')
    container_identifier = models.CharField(max_length=150, verbose_name="ID o VMID") 
    name = models.CharField(max_length=150)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNKNOWN')
    
    memory_limit = models.CharField(max_length=50, blank=True, null=True, verbose_name="Límite de RAM")
    cpu_cores = models.IntegerField(blank=True, null=True, verbose_name="Núcleos de CPU")

    def __str__(self):
        return f"{self.name} ({self.host.name})"


class LatencyLog(models.Model):
    node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='latency_logs')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    latency_ms = models.FloatField(null=True, blank=True)
    packet_loss_pct = models.FloatField(default=0.0, verbose_name="% Pérdida de Paquetes")
    is_online = models.BooleanField(default=False)

    # ELIMINAMOS CAMPOS DE TRÁFICO SNMP
    # inbound_mbps - ELIMINADO
    # outbound_mbps - ELIMINADO

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Registro de Latencia"
        verbose_name_plural = "Registros de Latencia"
        indexes = [
            models.Index(fields=['node', '-timestamp']),
        ]

    def __str__(self):
        estado = "Online" if self.is_online else "Offline"
        return f"{self.node.name} - {estado} a las {self.timestamp.strftime('%H:%M:%S')}"


class AlertEvent(models.Model):
    node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, null=True, blank=True)
    container = models.ForeignKey(Container, on_delete=models.CASCADE, null=True, blank=True)
    
    event_type = models.CharField(max_length=50, help_text="Ej. DOWN, RECOVERY, HIGH_LATENCY")
    message = models.TextField()
    
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        estado = "Resuelta" if self.is_resolved else "Activa"
        return f"Alerta ({estado}): {self.event_type}"

class HTTPEndpoint(models.Model):
    SERVICE_TYPES = [
        ('WEB', '🌐 Sitio Web / Aplicación Web'),
        ('API', '🔌 API / REST API'),
        ('NVR_CAM', '📹 NVR / Cámara IP'),
        ('DATABASE', '🗄️ Base de Datos (Web)'),
        ('FILE', '📁 Servidor de Archivos'),
        ('EMAIL', '📧 Servidor de Correo'),
        ('DNS', '🌍 Servidor DNS'),
        ('PROXY', '🔄 Proxy / Reverse Proxy'),
        ('LOAD_BALANCER', '⚖️ Balanceador de Carga'),
        ('OTHER', '❓ Otro'),
    ]
    
    STATUS_CHOICES = [
        ('UP', 'En línea'),
        ('DOWN', 'Caído'),
        ('WARN', 'Advertencia'),
        ('UNKNOWN', 'Desconocido'),
    ]
    
    name = models.CharField(max_length=150, verbose_name="Nombre del Servicio")
    url = models.URLField(verbose_name="URL del Servicio")
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, default='WEB', verbose_name="Tipo de Servicio")
    expected_status = models.IntegerField(default=200, verbose_name="Código HTTP esperado")
    timeout = models.IntegerField(default=5, verbose_name="Timeout (segundos)")
    check_ssl = models.BooleanField(default=True, verbose_name="Verificar SSL")
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNKNOWN')
    last_response_time = models.FloatField(null=True, blank=True, verbose_name="Último tiempo de respuesta (ms)")
    ssl_expiry_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha expiración SSL")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notify_telegram = models.BooleanField(default=True, verbose_name="Notificar por Telegram")
    down_since = models.DateTimeField(null=True, blank=True, verbose_name="Caído desde")
    recovered_at = models.DateTimeField(null=True, blank=True, verbose_name="Recuperado a las")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.url})"
    
    def get_service_type_display(self):
        return dict(self.SERVICE_TYPES).get(self.service_type, self.service_type)

class HTTPLog(models.Model):
    endpoint = models.ForeignKey(HTTPEndpoint, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(verbose_name="Tiempo de respuesta (ms)")
    is_online = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    ssl_valid = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['endpoint', '-timestamp']),
        ]
    
    def __str__(self):
        estado = "Online" if self.is_online else "Offline"
        return f"{self.endpoint.name} - {estado} a las {self.timestamp.strftime('%H:%M:%S')}"