from django.shortcuts import render, redirect
from .models import Homework, Submission
from django.contrib.auth.decorators import login_required

@login_required
def homework_list_student(request):
    student_class = request.user.profile.student_class  # assume profile has student_class
    homeworks = Homework.objects.filter(class_name=student_class)
    return render(request, 'homework/student_homework_list.html', {'homeworks': homeworks})

@login_required
def homework_create_teacher(request):
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        class_name = request.POST['class_name']
        subject = request.POST['subject']
        due_date = request.POST['due_date']
        Homework.objects.create(
            title=title,
            description=description,
            assigned_by=request.user,
            class_name=class_name,
            subject=subject,
            due_date=due_date
        )
        return redirect('homework:teacher_list')
    return render(request, 'homework/teacher_homework_create.html')

@login_required
def homework_list_teacher(request):
    homeworks = Homework.objects.filter(assigned_by=request.user)
    return render(request, 'homework/teacher_homework_list.html', {'homeworks': homeworks})