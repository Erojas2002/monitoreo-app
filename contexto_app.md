# 📡 Centro de Monitoreo de Red (NMS Ligero)

## 📝 Descripción General
Sistema de Gestión de Red (NMS) desarrollado para monitorear el estado, la latencia de dispositivos de red y servicios web en tiempo real. Diseñado con una arquitectura asíncrona para no bloquear el servidor durante los escaneos masivos.

## 🛠️ Stack Tecnológico
*   **Backend:** Python con Django y Django REST Framework (DRF).
*   **Base de Datos:** PostgreSQL.
*   **Tareas Asíncronas:** Celery + Celery Beat (Broker/Backend: Redis).
*   **Protocolos de Red:** `ping3` (ICMP), `requests` (HTTP/HTTPS).
*   **Notificaciones:** Telegram Bot API.
*   **Reportes:** ReportLab (PDF), OpenPyXL (Excel).
*   **Frontend:** HTML5, Tailwind CSS (estilos glassmorphism), JavaScript Vanilla.
*   **Visualización de Datos:** Chart.js (Gráficas duales) y GSAP (Animaciones fluidas).

---

## 🚀 Funcionalidades Implementadas

### 1. Gestión de Nodos (CRUD)
*   Registro de dispositivos con IP, Nombre, Tipo (Router, Switch, NVR, Cámara, Servidor).
*   Panel visual dinámico que refleja el estado actual (`UP`, `DOWN`, `WARN`).
*   Control individual de notificaciones por Telegram por dispositivo.
*   Monitoreo activo siempre habilitado (sin opción de desactivar).

### 2. Monitoreo ICMP (Ping y Latencia) - Optimizado
*   Escaneo programado vía Celery de todos los nodos activos.
*   Cálculo de latencia media y porcentaje de pérdida de paquetes.
*   **Optimizaciones:**
    *   Reducción de pings de 4 a 3 por nodo.
    *   Intervalo reducido entre pings (200ms → 100ms).
    *   Timeouts ajustados para respuesta más rápida.
*   Cambio de estado automático y registro histórico en la base de datos.
*   Registro de timestamp de caída y recuperación.

### 3. Monitoreo de Servicios Web (HTTP/HTTPS)
*   Verificación de disponibilidad de servicios web y APIs.
*   Medición de tiempo de respuesta (ms).
*   Verificación de certificados SSL con alertas de expiración (7 y 30 días).
*   Clasificación por tipo de servicio: WEB, API, NVR/Cámara, Base de Datos, etc.
*   Alertas automáticas para errores HTTP (400, 404, 500, 502, 503, etc.).
*   Control individual de notificaciones por Telegram por servicio.

### 4. Dashboard y Analítica en Tiempo Real
*   Interfaz de usuario responsiva con actualizaciones dinámicas configurables (10s, 20s, 30s, 1m).
*   **Gráficas duales (Chart.js):**
    *   **Calidad de Conexión:** Latencia en ms vs Pérdida de paquetes en %.
    *   **Disponibilidad (Uptime):** Histórico de disponibilidad por día (últimos 7 días).
*   Visualización clara del estado de cada dispositivo y servicio.
*   Pausa automática de actualizaciones al abrir formularios.

### 5. Sistema de Alertas y Notificaciones
*   **Alertas por Telegram:**
    *   Caída y recuperación de nodos de red.
    *   Caída y recuperación de servicios web.
    *   Errores HTTP (404, 500, 502, etc.).
    *   Certificados SSL próximos a expirar (7 y 30 días).
    *   Latencia alta y pérdida de paquetes.
*   **Control granular:** Activación/desactivación de notificaciones por dispositivo/servicio.
*   Registro histórico de eventos de alerta en base de datos.

### 6. Historial de Alertas con Filtros
*   Página dedicada con listado completo de alertas.
*   Filtros por tipo de alerta, estado (pendiente/resuelta), rango de fechas.
*   Estadísticas en tiempo real: total, pendientes, resueltas, tasa de resolución.
*   Actualización automática cada 30 segundos.

### 7. Predicciones de Fallos (Análisis Predictivo)
*   Detección de patrones anómalos basados en datos históricos.
*   **Tipos de predicciones:**
    *   Incremento gradual de latencia (+50%).
    *   Caídas frecuentes (3+ en última semana).
    *   Alta pérdida de paquetes (>20%).
    *   Patrones de caída (misma hora recurrentemente).
*   Clasificación por severidad: CRITICAL, WARNING, INFO.

### 8. Reportes (PDF y Excel)
*   **Reporte PDF:** Estadísticas generales, detalle de nodos, servicios web.
*   **Reporte Excel:** Hojas separadas para Nodos, Servicios Web y Alertas.
*   Exportación con un solo clic desde el dashboard.

### 9. Gestión de Servicios Web (CRUD)
*   Registro de servicios con nombre, URL, tipo, timeout y verificación SSL.
*   Panel visual con indicadores de estado, respuesta y SSL.
*   Clasificación por tipo de servicio para mejor organización.

---

## ⚙️ Configuración Clave del Entorno

### Variables de Entorno
```python
# Telegram Configuration
# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'Tu token')  
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'Tu chat_id')

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