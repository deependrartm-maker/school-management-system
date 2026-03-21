from django.urls import path
from . import views

urlpatterns = [
    path('teacher/attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance/<int:student_id>/', views.view_attendance, name='view_attendance'),
]