📡 Centro de Monitoreo de Red (NMS Ligero)
📝 Descripción General
Sistema de Gestión de Red (NMS) desarrollado para monitorear el estado y la latencia de dispositivos de red en tiempo real. Diseñado con una arquitectura asíncrona para no bloquear el servidor durante los escaneos masivos. Versión actual enfocada en monitoreo ICMP con detección inteligente y rendimiento optimizado.

🛠️ Stack Tecnológico
Backend: Python con Django y Django REST Framework (DRF).

Base de Datos: PostgreSQL.

Tareas Asíncronas: Celery + Celery Beat (Broker/Backend: Redis).

Protocolos de Red: ping3 (ICMP).

Frontend: HTML5, Tailwind CSS (estilos glassmorphism), JavaScript Vanilla.

Visualización de Datos: Chart.js (Gráfica única) y GSAP (Animaciones fluidas).

🚀 Funcionalidades Implementadas Hasta la Fecha
1. Gestión de Nodos (CRUD)
Registro de dispositivos con IP, Nombre, Tipo (Router, Switch, NVR, Cámara, Servidor) y estado de monitoreo.

Panel visual dinámico que refleja el estado actual (UP, DOWN, WARN).

Interfaz simplificada sin configuraciones complejas.

2. Monitoreo ICMP (Ping y Latencia) - Optimizado
Escaneo programado vía Celery de todos los nodos activos.

Cálculo de latencia media y porcentaje de pérdida de paquetes.

Optimizaciones de rendimiento:

Reducción de pings de 4 a 3 por nodo para mayor velocidad.

Intervalo reducido entre pings (200ms → 100ms).

Timeouts ajustados para respuesta más rápida.

Cambio de estado automático y registro histórico en la base de datos.

3. Dashboard y Analítica en Tiempo Real
Interfaz de usuario responsiva con actualizaciones dinámicas configurables (10s, 20s, 30s, 1m).

Gráfica de área única (Chart.js):

Calidad de conexión: Latencia en ms vs Pérdida de paquetes en %.

Visualización clara del estado de cada dispositivo.

4. Sistema de Alertas
Notificaciones automáticas cuando un nodo cambia a estado DOWN.

Recuperación automática cuando un nodo vuelve a estar UP.

Registro histórico de eventos de alerta.

⚙️ Configuración Clave del Entorno
Celery Beat: Configurado para disparar la tarea run_network_monitor cada 10 segundos.

Monitoreo ICMP: Pings concurrentes con timeout de 1 segundo por dispositivo.

📈 Mejoras Recientes (Agosto 2026)
Optimización de Rendimiento
Monitoreo acelerado: Reducción del tiempo de escaneo en ~30%.

Detección inteligente: Sistema más rápido y eficiente en la verificación de nodos.

Código simplificado: Eliminación de dependencias y complejidad innecesaria.

Limpieza y Simplificación
Eliminación de SNMP: Sistema enfocado en monitoreo ICMP para mayor simplicidad.

Código más limpio: Eliminados servicios, modelos y dependencias relacionadas con SNMP.

Frontend optimizado: Gráfica única más clara y enfocada en métricas de conectividad.

🗺️ Próximos Pasos (Roadmap)
□ Integración con Proxmox API: Leer recursos de hardware (CPU/RAM) de contenedores LXC y Máquinas Virtuales.
□ Sistema de Alertas (Telegram): Configurar notificaciones push para caídas de nodos y recuperaciones.
□ Historial de Rendimiento: Almacenamiento y visualización de tendencias a largo plazo.
□ Monitoreo de Ancho de Banda (Alternativo): Evaluación de NetFlow/sFlow o APIs de dispositivos.
📊 Estadísticas de Rendimiento
Tiempo de escaneo por nodo: ~1-2 segundos.

Frecuencia de monitoreo: Configurable desde 10 segundos hasta 1 minuto.

Retención de datos: Historial completo de latencia y eventos.

Escalabilidad: Soporte para múltiples dispositivos con escaneo eficiente.

🔧 Notas Técnicas
Migraciones: Base de datos actualizada para reflejar los cambios en el modelo (eliminación de campos SNMP).

Dependencias: Solo ping3 para monitoreo ICMP, sin dependencias adicionales.

Despliegue: Compatible con entornos de producción mediante Celery y Redis.