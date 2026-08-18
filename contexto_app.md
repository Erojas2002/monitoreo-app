Centro de Monitoreo de Red (NMS Ligero)Descripción General
Sistema de Gestión de Red (NMS) desarrollado para monitorear el estado, la latencia de dispositivos de red y servicios web en tiempo real. Diseñado con una arquitectura asíncrona para no bloquear el servidor durante los escaneos masivos. Incluye un sistema completo de alertas por Telegram, predicciones de fallos, reportes y configuración dinámica.
Stack Tecnológico
Backend: Python con Django y Django REST Framework (DRF).

Base de Datos: PostgreSQL.

Tareas Asíncronas: Celery + Celery Beat (Broker/Backend: Redis).

Protocolos de Red: ping3 (ICMP), requests (HTTP/HTTPS).

Notificaciones: Telegram Bot API con configuración dinámica desde interfaz.

Reportes: ReportLab (PDF), OpenPyXL (Excel).

Frontend: HTML5, Tailwind CSS (estilos glassmorphism), JavaScript Vanilla (modularizado en archivos estáticos).

Visualización de Datos: Chart.js (Gráficas duales) y GSAP (Animaciones fluidas).

Funcionalidades Implementadas
1. Gestión de Nodos (CRUD)
Registro de dispositivos con IP, Nombre, Tipo (Router, Switch, NVR, Cámara, Servidor).

Panel visual dinámico que refleja el estado actual (UP, DOWN, WARN).

Control individual de notificaciones por Telegram por dispositivo.

Monitoreo activo siempre habilitado (sin opción de desactivar).

2. Monitoreo ICMP (Ping y Latencia) - Optimizado
Escaneo programado vía Celery de todos los nodos activos.

Cálculo de latencia media y porcentaje de pérdida de paquetes.

Optimizaciones:

Reducción de pings de 4 a 3 por nodo.

Intervalo reducido entre pings (200ms → 100ms).

Timeouts ajustados para respuesta más rápida.

Cambio de estado automático y registro histórico en la base de datos.

Registro de timestamp de caída y recuperación.

3. Monitoreo de Servicios Web (HTTP/HTTPS)
Verificación de disponibilidad de servicios web y APIs.

Medición de tiempo de respuesta (ms).

Verificación de certificados SSL con alertas de expiración (7 y 30 días).

Clasificación por tipo de servicio: WEB, API, NVR/Cámara, Base de Datos, Servidor de Archivos, Correo, DNS, Proxy, Balanceador de Carga.

Alertas automáticas para errores HTTP (400, 401, 403, 404, 405, 408, 500, 501, 502, 503, 504, 505).

Control individual de notificaciones por Telegram por servicio.

4. Dashboard y Analítica en Tiempo Real
Interfaz de usuario responsiva con actualizaciones dinámicas configurables (10s, 20s, 30s, 1m).

Sistema de pestañas (tabs) para navegar entre: Nodos de Red, Servicios Web y Predicciones.

Paginación independiente por sección (8, 16, 24, 32 elementos para nodos y servicios; 4, 8, 12, 16 para predicciones).

Filtros de búsqueda en tiempo real para cada sección (por nombre, IP, URL, tipo, etc.).

Gráficas duales (Chart.js):

Calidad de Conexión: Latencia en ms vs Pérdida de paquetes en %.

Disponibilidad (Uptime): Histórico de disponibilidad por día (últimos 7 días).

Pausa automática de actualizaciones al abrir formularios.

5. Sistema de Alertas y Notificaciones
Alertas por Telegram:

Caída y recuperación de nodos de red.

Caída y recuperación de servicios web.

Errores HTTP específicos (404, 500, 502, etc.).

Certificados SSL próximos a expirar (7 y 30 días).

Latencia alta y pérdida de paquetes.

Control granular: Activación/desactivación de notificaciones por dispositivo/servicio.

Registro histórico de eventos de alerta en base de datos.

Fechas de caída y recuperación con cálculo de tiempo de inactividad.

6. Historial de Alertas con Filtros y Paginación
Página dedicada con listado completo de alertas.

Filtros por tipo de alerta, estado (pendiente/resuelta), rango de fechas.

Botón "Resolver" manual para marcar alertas como resueltas.

Estadísticas en tiempo real: total, pendientes, resueltas, tasa de resolución.

Paginación con opciones de 10, 20, 50, 100 elementos por página.

Actualización automática cada 60 segundos.

7. Predicciones de Fallos (Análisis Predictivo)
Detección de patrones anómalos basados en datos históricos.

Tipos de predicciones:

Incremento gradual de latencia (+50%).

Caídas frecuentes (3+ en última semana).

Alta pérdida de paquetes (>20%).

Patrones de caída (misma hora recurrentemente).

Clasificación por severidad: CRITICAL, WARNING, INFO.

Colores diferenciados: rojo para crítico, naranja para advertencia, azul para informativo.

8. Reportes (PDF y Excel)
Reporte PDF: Estadísticas generales, detalle de nodos, servicios web.

Reporte Excel: Hojas separadas para Nodos, Servicios Web y Alertas.

Exportación con un solo clic desde el panel de control.

9. Gestión de Servicios Web (CRUD)
Registro de servicios con nombre, URL, tipo, timeout y verificación SSL.

Panel visual con indicadores de estado, respuesta y SSL.

Clasificación por tipo de servicio para mejor organización.

Código HTTP fijo en 200 (automático, sin configuración manual).

10. Configuración Dinámica de Telegram
Página de ajustes para configurar Token del Bot y Chat ID.

Campos sensibles ocultos con asteriscos (visibles solo con botón "Mostrar").

Envío de mensaje de prueba para verificar configuración.

Guardado en base de datos, sin necesidad de modificar código.

Fallback a variables de entorno si no hay configuración en BD.

Notificaciones con timestamps y formato de hora local (Venezuela, UTC-4).

11. Organización de Código Frontend
Archivos CSS y JavaScript separados en carpeta static/.

dashboard.js: Lógica principal del dashboard.

alerts.js: Lógica de historial de alertas.

settings.js: Lógica de configuración de Telegram.

styles.css: Estilos globales reutilizables.

Configuración Clave del Entorno:

Variables de Entorno
python
# Zona horaria (Venezuela)
TIME_ZONE = 'America/Caracas'
USE_TZ = True

# Telegram (fallback si no hay configuración en BD)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'network-monitor': {
        'task': 'monitoreo_app.tasks.run_network_monitor',
        'schedule': 10.0,  # Cada 10 segundos
    },
    'http-monitor': {
        'task': 'monitoreo_app.tasks.run_http_monitor',
        'schedule': 30.0,  # Cada 30 segundos
    },
}
Archivos Estáticos
python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'monitoreo_app/static'),
]

Funciones Más Importantes del Sistema
Backend - Servicios
network_monitor.py

check_all_nodes(): Función principal que ejecuta el monitoreo ICMP de todos los nodos activos. Realiza 3 pings por nodo, calcula latencia y pérdida de paquetes, actualiza estados y dispara alertas.

handle_status_change(): Gestiona los cambios de estado de los nodos (DOWN, UP, WARN). Crea eventos de alerta, envía notificaciones por Telegram y calcula tiempo de inactividad.

format_datetime(): Formatea fechas con zona horaria local (Venezuela, UTC-4) para mensajes de alerta.

http_monitor.py

check_all_http_endpoints(): Función principal que verifica todos los servicios web activos mediante peticiones HTTP/HTTPS.

check_ssl_expiry(): Monitorea fechas de expiración de certificados SSL y envía alertas cuando faltan 7 o 30 días.

handle_http_error(): Maneja códigos de error HTTP específicos (400, 404, 500, 502, 503, etc.) y genera alertas.

handle_http_status_change(): Gestiona cambios de estado de servicios web (caída, recuperación, lentitud).

telegram_service.py

TelegramNotifier: Clase principal para enviar mensajes a Telegram con soporte síncrono y asíncrono.

send_alert_sync(): Envía alertas formateadas con emojis y estructura clara.

get_telegram_notifier(): Obtiene la instancia del notificador con la configuración actual (desde BD o variables de entorno).

prediction_service.py

predict_node_failures(): Analiza logs históricos (7 días) y detecta patrones de posible fallo.

get_node_health_score(): Calcula un puntaje de salud (0-100) basado en disponibilidad, latencia, pérdida de paquetes y caídas recientes.

report_service.py

generate_nodes_report_pdf(): Genera reporte PDF con estadísticas y detalle de nodos y servicios web.

generate_excel_report(): Genera reporte Excel con hojas separadas para nodos, servicios y alertas.

Backend - Vistas y API
views.py

NetworkNodeViewSet: CRUD completo de nodos con endpoints personalizados para histórico (/history/), métricas (/metrics/), predicciones (/predictions/) y salud (/health/).

AlertEventViewSet: Gestión de alertas con endpoints para filtrado (/filter/) y estadísticas (/stats/).

HTTPEndpointViewSet: CRUD completo de servicios web.

ReportViewSet: Endpoints para descarga de reportes PDF y Excel.

settings_view: Vista para configuración de Telegram con almacenamiento en base de datos.

Frontend - JavaScript
dashboard.js

cargarNodos(), cargarServiciosHTTP(), cargarPredicciones(): Funciones principales de carga con paginación y filtros.

renderizarNodos(), renderizarServiciosHTTP(), renderizarPredicciones(): Renderizado dinámico de tarjetas con animaciones GSAP.

abrirModal(), abrirModalHTTP(): Apertura de formularios con pausa de actualizaciones.

guardarNodo(), guardarServicioHTTP(): Envío de datos al backend con manejo de errores.

cambiarTab(): Navegación entre pestañas (Nodos, Servicios, Predicciones).

filtrarNodos(), filtrarServicios(), filtrarPredicciones(): Filtros en tiempo real por búsqueda.

abrirGraficas(), cerrarGraficas(): Apertura y cierre de gráficas con Chart.js.

alerts.js

cargarAlertas(): Carga de alertas con filtros y paginación.

marcarComoResuelta(): Actualización manual de estado de alertas vía PATCH.

renderizarAlertas(): Renderizado de tarjetas con botón de resolución.

settings.js

mostrarCampo(), ocultarCampo(): Control de visibilidad de campos sensibles (Token y Chat ID).

enviarPrueba(): Envío de mensaje de prueba a Telegram desde la interfaz.

Modelos de Datos Principales
NetworkNode: Dispositivos de red con IP, tipo, estado, notificaciones y timestamps de caída/recuperación.

HTTPEndpoint: Servicios web con URL, tipo, timeout, SSL, estado y notificaciones.

LatencyLog: Historial de latencia y pérdida de paquetes por nodo.

HTTPLog: Historial de respuestas HTTP y errores por servicio.

AlertEvent: Registro de eventos y alertas generadas.

AppSettings: Configuración dinámica de Telegram.

Estadísticas de Rendimiento
Tiempo de escaneo por nodo: ~1-2 segundos.

Frecuencia de monitoreo: Configurable desde 10 segundos hasta 1 minuto.

Retención de datos: Historial completo de latencia, eventos y logs HTTP.

Escalabilidad: Soporte para múltiples dispositivos con escaneo eficiente.

Notas Técnicas
Migraciones: Base de datos actualizada con modelos para nodos, servicios web, alertas y configuración.

Dependencias: ping3 para ICMP, requests para HTTP, python-telegram-bot para notificaciones, reportlab y openpyxl para reportes.

Despliegue: Compatible con entornos de producción mediante Celery y Redis.

Arquitectura Frontend: HTML con herencia de plantillas, JavaScript modularizado en archivos estáticos, estilos centralizados.

Seguridad: Tokens CSRF, campos sensibles ocultos en interfaz, configuración dinámica sin exposición de credenciales en código.

Cómo Probar:

Clonar el repositorio.

Configurar variables de entorno (Base de Datos, Redis).

Aplicar migraciones y configurar archivos estáticos.

Iniciar Celery Worker y Beat para monitoreo automático.

Ejecutar el servidor Django y acceder a la interfaz web.

bash
# Terminal 1 - Celery Worker
celery -A monitoreo_proyecto worker -l INFO --pool=solo

# Terminal 2 - Celery Beat
celery -A monitoreo_proyecto beat -l INFO     

# Terminal 3 - Servidor Django
python manage.py runserver