from audit.models import BlockedIP
from django.http import HttpResponseForbidden
from django.utils import timezone
from audit.utils import get_client_ip


class IPBlockMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = get_client_ip(request)

        try:
            blocked = BlockedIP.objects.get(ip_address=ip)
            if blocked.is_active():
                return HttpResponseForbidden("Your IP is temporarily blocked.")
            else:
                blocked.delete()
        except BlockedIP.DoesNotExist:
            pass

        return self.get_response(request)