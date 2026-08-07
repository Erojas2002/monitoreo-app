# monitoreo_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from .views import (
    NetworkNodeViewSet, 
    VirtualHostViewSet, 
    ContainerViewSet, 
    LatencyLogViewSet, 
    AlertEventViewSet,
    HTTPEndpointViewSet
)

# El router de DRF crea automáticamente las URLs para los ViewSets
router = DefaultRouter()
router.register(r'nodes', NetworkNodeViewSet)
router.register(r'hosts', VirtualHostViewSet)
router.register(r'containers', ContainerViewSet)
router.register(r'latency-logs', LatencyLogViewSet)
router.register(r'alerts', AlertEventViewSet)
router.register(r'http-endpoints', HTTPEndpointViewSet)

urlpatterns = [
    path('', TemplateView.as_view(template_name='monitoreo_app/dashboard.html'), name='dashboard'),
    path('api/', include(router.urls)),
]