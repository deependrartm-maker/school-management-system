from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('student/', views.homework_list_student, name='student_list'),
    path('teacher/', views.homework_list_teacher, name='teacher_list'),
    path('teacher/create/', views.homework_create_teacher, name='teacher_create'),
]