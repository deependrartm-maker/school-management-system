from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class ActivityLog(models.Model):

    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('MARKS_ENTRY', 'Marks Entry'),
        ('ATTENDANCE_MARK', 'Attendance Mark'),
        ('RESULT_LOCK', 'Result Lock'),
        ('FAILED_LOGIN', 'IP_BLOCKED'),  # ✅ NEW (STEP 11.4)
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    action_type = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES
    )

    description = models.TextField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action_type']),
            models.Index(fields=['timestamp']),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise Exception("Audit logs are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise Exception("Audit logs cannot be deleted.")

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.timestamp}"
    
class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    blocked_at = models.DateTimeField(auto_now_add=True)
    unblock_at = models.DateTimeField()

    def is_active(self):
        return timezone.now() < self.unblock_at

    def __str__(self):
        return f"{self.ip_address} blocked until {self.unblock_at}"    
    
