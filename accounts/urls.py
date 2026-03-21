from django.urls import path
from accounts import views as accounts_views
from .views import login_view, logout_view

urlpatterns = [
    path('login/', accounts_views.login_view, name='login'),
    path('dashboard/admin/', accounts_views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/teacher/', accounts_views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/student/', accounts_views.student_dashboard, name='student_dashboard'),
    path('dashboard/parent/', accounts_views.parent_dashboard, name='parent_dashboard'),
    path('logout/', logout_view, name='logout'),
]