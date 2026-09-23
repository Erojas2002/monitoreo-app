# monitoreo_app/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """
    Decorador que verifica que el usuario sea administrador.
    Un usuario es administrador si:
    - Es superusuario (is_superuser)
    - Es staff (is_staff)
    - Su perfil tiene rol ADMIN
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificar si es administrador
        is_admin = (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN')
        )
        
        if not is_admin:
            messages.error(request, '❌ No tienes permisos para acceder a esta sección')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def operator_required(view_func):
    """
    Decorador que verifica que el usuario sea operador o administrador.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        is_operator_or_admin = (
            request.user.is_superuser or 
            request.user.is_staff or
            (hasattr(request.user, 'profile') and request.user.profile.role in ['ADMIN', 'OPERATOR'])
        )
        
        if not is_operator_or_admin:
            messages.error(request, '❌ No tienes permisos para realizar esta acción')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper