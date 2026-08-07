# monitoreo_proyecto/celery.py
import os
from celery import Celery

# Establecer el módulo de configuración de Django por defecto para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoreo_proyecto.settings')

app = Celery('monitoreo_proyecto')

# Usar una cadena aquí significa que el worker no tiene que serializar
# el objeto de configuración. Namespace 'CELERY' significa que todas 
# las claves de configuración de celery deben tener el prefijo `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas de todas las aplicaciones registradas en Django
app.autodiscover_tasks()