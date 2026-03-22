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

from django.shortcuts import render, get_object_or_404, redirect
from .models import Homework, HomeworkSubmission
from .forms import HomeworkSubmissionForm

# STUDENT: Submit Homework
@login_required
def submit_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)

    # Check if already submitted
    existing = HomeworkSubmission.objects.filter(
        homework=homework,
        student=request.user
    ).first()

    if request.method == 'POST':
        form = HomeworkSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.homework = homework
            submission.student = request.user
            submission.save()
            return redirect('student_homework_list')
    else:
        form = HomeworkSubmissionForm()

    return render(request, 'homework/submit_homework.html', {
        'form': form,
        'homework': homework,
        'existing': existing
    })


# TEACHER: View Submissions
@login_required
def view_submissions(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    submissions = HomeworkSubmission.objects.filter(homework=homework)

    return render(request, 'homework/view_submissions.html', {
        'homework': homework,
        'submissions': submissions
    })