# monitoreo_app/tasks.py
from celery import shared_task
from .services.network_monitor import check_all_nodes
from .services.http_monitor import check_all_http_endpoints

@shared_task
def run_network_monitor():
    """
    Tarea asíncrona que envuelve nuestra lógica de monitoreo.
    Celery Beat se encargará de llamarla periódicamente.
    """
    check_all_nodes()
    return "Monitoreo de red completado exitosamente"

@shared_task
def run_http_monitor():
    """
    Tarea para monitorear endpoints HTTP/HTTPS
    """
    check_all_http_endpoints()
    return "Monitoreo HTTP completado exitosamente"