from .base import *

# ==============================
# DEVELOPMENT SETTINGS
# ==============================

DEBUG = True

ALLOWED_HOSTS = []

# 🔑 IMPORTANT – Add Secret Key for Local Dev
SECRET_KEY = "django-dev-secret-key-very-secure-123456"

# ==============================
# DATABASE (SQLite for Local)
# ==============================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================
# EMAIL (Console for Dev)
# ==============================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==============================
# SECURITY (Relaxed for Dev)
# ==============================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False