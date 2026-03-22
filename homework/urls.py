from django.urls import path
from . import views

app_name = 'homework'

urlpatterns = [
    path('student/', views.homework_list_student, name='student_list'),
    path('teacher/', views.homework_list_teacher, name='teacher_list'),
    path('teacher/create/', views.homework_create_teacher, name='teacher_create'),
    path('submit/<int:homework_id>/', views.submit_homework, name='submit_homework'),
    path('submissions/<int:homework_id>/', views.view_submissions, name='view_submissions'),
]