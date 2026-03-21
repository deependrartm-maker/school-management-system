from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import date
from profiles.models import StudentProfile
from .models import AttendanceRecord
from accounts.decorators import role_required
from .permissions import can_view_attendance
from datetime import date, datetime
from audit.utils import log_activity


@login_required
@role_required('TEACHER')
@login_required
@role_required('TEACHER')
def mark_attendance(request):
    selected_date = date.today()

    if request.method == 'POST':
        selected_date = datetime.strptime(
            request.POST.get('attendance_date'),
            '%Y-%m-%d'
        ).date()

    students = StudentProfile.objects.all()

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'student_{student.id}')
            if status:
                record, created = AttendanceRecord.objects.get_or_create(
                    student=student,
                    date=selected_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user
                    }
                )

                if created:
                    log_activity(
                        user=request.user,
                        action_type='ATTENDANCE_MARK',
                        description=f"{request.user.email} marked attendance for {student.user.email} on {selected_date}"
                    )

        return redirect('mark_attendance')

    return render(request, 'attendance/mark.html', {
        'students': students,
        'selected_date': selected_date
    })


@login_required
def view_attendance(request, student_id):
    student = StudentProfile.objects.get(id=student_id)

    if not can_view_attendance(request.user, student):
        return render(request, '403.html', status=403)

    records = student.attendance_records.all()
    return render(request, 'attendance/view.html', {
        'student': student,
        'records': records
    })