from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Forbidden")

            return view_func(request, *args, **kwargs)
        return wrapper_func
    return decorator

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == "ADMIN":
            return view_func(request, *args, **kwargs)
        return redirect("login")
    return wrapper