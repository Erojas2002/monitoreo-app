# monitoreo_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from .views import (
    NetworkNodeViewSet, 
    VirtualHostViewSet, 
    ContainerViewSet, 
    LatencyLogViewSet, 
    AlertEventViewSet,
    HTTPEndpointViewSet,
    ReportViewSet,
    UserProfileViewSet,
    settings_view,
    test_telegram
)
from .decorators import admin_required

router = DefaultRouter()
router.register(r'nodes', NetworkNodeViewSet)
router.register(r'hosts', VirtualHostViewSet)
router.register(r'containers', ContainerViewSet)
router.register(r'latency-logs', LatencyLogViewSet)
router.register(r'alerts', AlertEventViewSet)
router.register(r'http-endpoints', HTTPEndpointViewSet)
router.register(r'users', UserProfileViewSet)

urlpatterns = [
    # ============================================
    # AUTENTICACIÓN
    # ============================================
    path('login/', auth_views.LoginView.as_view(
        template_name='monitoreo_app/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # ============================================
    # VISTAS PROTEGIDAS
    # ============================================
    path('', login_required(TemplateView.as_view(
        template_name='monitoreo_app/dashboard.html'
    )), name='dashboard'),
    
    path('alerts/', login_required(TemplateView.as_view(
        template_name='monitoreo_app/alerts.html'
    )), name='alerts'),
    
    # Solo admin puede acceder a ajustes
    path('settings/', settings_view, name='settings'),
    
    # ============================================
    # API
    # ============================================
    path('api/', include(router.urls)),
    path('api/test-telegram/', test_telegram, name='test-telegram'),
    path('api/reports/', include([
        path('pdf/', ReportViewSet.as_view({'get': 'pdf'}), name='report_pdf'),
        path('excel/', ReportViewSet.as_view({'get': 'excel'}), name='report_excel'),
    ])),
]