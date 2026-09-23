# monitoreo_app/serializers.py
from rest_framework import serializers
from .models import NetworkNode, VirtualHost, Container, LatencyLog, AlertEvent, HTTPEndpoint, HTTPLog, UserProfile
from django.contrib.auth.models import User

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

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_active', 'is_staff']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name', 'password',
            'role', 'telegram_bot_token', 'telegram_chat_id',
            'notify_node_down', 'notify_node_recovery', 
            'notify_http_down', 'notify_http_recovery',
            'notify_ssl_expiry', 'notify_high_latency',
            'is_active', 'has_telegram_configured', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'has_telegram_configured']
        extra_kwargs = {
            'telegram_bot_token': {'required': False, 'allow_blank': True, 'allow_null': True},
            'telegram_chat_id': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
    
    def validate_username(self, value):
        """Valida que el username no exista (solo al crear)"""
        if value:
            # Si estamos actualizando, excluimos el usuario actual
            if self.instance:
                if User.objects.filter(username=value).exclude(id=self.instance.user.id).exists():
                    raise serializers.ValidationError('Este nombre de usuario ya existe')
            else:
                if User.objects.filter(username=value).exists():
                    raise serializers.ValidationError('Este nombre de usuario ya existe')
        return value
    
    def create(self, validated_data):
        # Extraer datos del usuario
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', '')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        password = validated_data.pop('password', None)
        
        if not username:
            raise serializers.ValidationError({'username': 'El nombre de usuario es requerido'})
        
        # Verificar si el usuario ya existe (por seguridad)
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Este nombre de usuario ya existe'})
        
        # Limpiar campos vacíos de Telegram
        if not validated_data.get('telegram_bot_token'):
            validated_data['telegram_bot_token'] = None
        if not validated_data.get('telegram_chat_id'):
            validated_data['telegram_chat_id'] = None
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password or 'changeme123'  # Password por defecto
        )
        
        # La señal post_save ya creó el UserProfile automáticamente
        # Ahora lo actualizamos con los datos adicionales
        profile = user.profile
        for attr, value in validated_data.items():
            setattr(profile, attr, value)
        profile.save()
        
        return profile
    
    def update(self, instance, validated_data):
        # Actualizar datos del usuario
        user = instance.user
        
        new_username = validated_data.pop('username', None)
        if new_username and new_username != user.username:
            # Verificar que no exista otro usuario con ese username
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                raise serializers.ValidationError({'username': 'Este nombre de usuario ya existe'})
            user.username = new_username
        
        user.email = validated_data.pop('email', user.email)
        user.first_name = validated_data.pop('first_name', user.first_name)
        user.last_name = validated_data.pop('last_name', user.last_name)
        
        password = validated_data.pop('password', None)
        if password:
            user.set_password(password)
        user.save()
        
        # Limpiar campos vacíos de Telegram
        if validated_data.get('telegram_bot_token') == '':
            validated_data['telegram_bot_token'] = None
        if validated_data.get('telegram_chat_id') == '':
            validated_data['telegram_chat_id'] = None
        
        # Actualizar perfil
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance