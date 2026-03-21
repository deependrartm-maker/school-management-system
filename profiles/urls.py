from django.urls import path
from . import views

urlpatterns = [
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
]