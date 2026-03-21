from .models import ActivityLog
from django.utils import timezone
from datetime import timedelta
from .models import  BlockedIP
from django.db.models import Count


def get_client_ip(request):
    """
    Handles proxy and local environments safely.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def log_activity(user, action_type, description, request=None):

    ip = None
    if request:
        ip = get_client_ip(request)

    ActivityLog.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        ip_address=ip
    )
def auto_block_ip(ip):
        window_start = timezone.now() - timedelta(minutes=15)

        failed_count = ActivityLog.objects.filter(
            action_type='FAILED_LOGIN',
            ip_address=ip,
            timestamp__gte=window_start
        ).count()

        if failed_count >= 5:
            unblock_time = timezone.now() + timedelta(minutes=30)

            BlockedIP.objects.update_or_create(
                ip_address=ip,
                defaults={'unblock_at': unblock_time}
            )