from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
# -------- Custom User Manager --------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


# -------- Custom User --------
class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('ADMIN','Admin'),
        ('TEACHER','Teacher'),
        ('STUDENT','Student'),
        ('PARENT','Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class AccountLock(models.Model):
        user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
        failed_attempts = models.IntegerField(default=0)
        is_locked = models.BooleanField(default=False)
        locked_at = models.DateTimeField(null=True, blank=True)

        LOCK_DURATION_MINUTES = 30

        def lock(self):
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save(update_fields=["is_locked", "locked_at"])

        def unlock(self):
            self.failed_attempts = 0
            self.is_locked = False
            self.locked_at = None
            self.save()

        def is_lock_active(self):
            if not self.is_locked:
                return False

            if not self.locked_at:
                return False

            expiry = self.locked_at + timedelta(minutes=self.LOCK_DURATION_MINUTES)

            if timezone.now() >= expiry:
                self.unlock()
                return False

            return True

        def __str__(self):
            return f"{self.user.email} - Locked: {self.is_locked}"