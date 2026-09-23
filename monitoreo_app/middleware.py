# monitoreo_app/middleware.py
from django.contrib.auth import logout
from django.contrib.auth.models import User


class ActiveUserMiddleware:
    """Verifica que el usuario de la sesión aún exista"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar que el usuario aún exista en la BD
            try:
                User.objects.get(pk=request.user.pk)
            except User.DoesNotExist:
                logout(request)
        
        response = self.get_response(request)
        return response