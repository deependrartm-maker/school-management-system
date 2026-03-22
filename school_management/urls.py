from django.contrib import admin
from django.urls import path, include

# ✅ NEW (for media files)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('accounts.urls')),
    path('', include('profiles.urls')),
    path('', include('attendance.urls')),

    path('dashboard/', include('dashboard.urls')),
    path('dashboard/admin/marks/', include('marks.urls', namespace='marks')),

    path('verify/', include('verification.urls')),

    # ✅ Homework URLs
    path('homework/', include('homework.urls')),
]

# ✅ VERY IMPORTANT (file upload ke liye)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)