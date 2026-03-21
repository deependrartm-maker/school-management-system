from django.urls import path
from .views import admin_security_dashboard
from . import views
from .views import (
    admin_dashboard,
    teacher_dashboard,
    student_dashboard,
    parent_dashboard
)

urlpatterns = [
    path('admin/', admin_dashboard, name='admin_dashboard'),
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('student/', student_dashboard, name='student_dashboard'),
    path('parent/', parent_dashboard, name='parent_dashboard'),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("classes/", views.class_overview, name="class_overview"),
    path("performance/", views.system_performance, name="system_performance"),
    path('admin-security/', admin_security_dashboard, name='admin_security_dashboard'),
    path('security/blocked-ips/', views.admin_blocked_ips, name='admin_blocked_ips'),
    path('security/unblock/<int:block_id>/', views.unblock_ip, name='unblock_ip'),
    path('security/manual-block/', views.manual_block_ip, name='manual_block_ip'),
    path('add_student/', views.add_student, name='add_student'),
    path('edit_student/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/', views.student_list, name='student_list'),
]

