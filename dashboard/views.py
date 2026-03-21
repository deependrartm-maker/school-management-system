from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render,get_object_or_404
from accounts.decorators import role_required
from profiles.models import StudentProfile
from marks.models import MarkRecord
from marks.models import Subject
from collections import defaultdict
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from audit.models import ActivityLog
from accounts.decorators import role_required
import json
from django.contrib import messages
from django.db.models.functions import TruncDate, ExtractHour
from accounts.decorators import admin_required
from marks.models import ResultLock
from marks.grade_utils import calculate_division
from audit.models import BlockedIP
from accounts.models import CustomUser
from profiles.models import StudentProfile, ParentProfile

@login_required(login_url="/login/")

@role_required("TEACHER")
def teacher_dashboard(request):

    class_name = request.GET.get("class")
    exam_name = request.GET.get("exam")

    topper = get_class_topper(class_name, exam_name)

    context = {
        "topper": topper,
        "selected_class": class_name,
        "selected_exam": exam_name,
    }

    return render(request, "dashboard/teacher.html", context)

@login_required(login_url="/login/")
@role_required("STUDENT")
def student_dashboard(request):

    student_profile = StudentProfile.objects.filter(
        user=request.user
    ).first()

    return render(
        request,
        "dashboard/student.html",
        {
            "student_profile": student_profile
        }
    )
      
@login_required(login_url="/login/")
@role_required("PARENT")
def parent_dashboard(request):
    return HttpResponse("PARENT DASHBOARD")


# ===============================
# DEBUG VERSION — CLASS TOPPER
# ===============================

# ===============================
# PRODUCTION VERSION — CLASS TOPPER
# ===============================

def get_class_topper(class_name, exam_name):
    """
    Returns topper dictionary:
    {
        student,
        percentage,
        division,
        result
    }

    Only works if ResultLock is locked.
    Safe, immutable-friendly, production ready.
    """

    if not class_name or not exam_name:
        return None

    # Show topper only if result is locked
    if not ResultLock.objects.filter(
        class_name=class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists():
        return None

    students = StudentProfile.objects.filter(class_name=class_name)

    highest_percentage = 0
    topper = None

    for student in students:

        records = MarkRecord.objects.filter(
            student=student,
            exam_name=exam_name
        )

        if not records.exists():
            continue

        totals = records.aggregate(
            total_obtained=Sum("marks_obtained"),
            total_max=Sum("total_marks")
        )

        total = totals["total_obtained"] or 0
        total_max = totals["total_max"] or 0

        if total_max == 0:
            continue

        percentage = (total / total_max) * 100

        if percentage > highest_percentage:
            highest_percentage = percentage
            topper = {
                "student": student,
                "percentage": round(percentage, 2),
                "division": calculate_division(percentage),
                "result": "PASS" if percentage >= 40 else "FAIL"
            }

    return topper

@role_required("ADMIN")
def admin_dashboard(request):

    # -------------------------------
    # Basic Counts
    # -------------------------------
    total_students = StudentProfile.objects.count()

    total_classes = (
        StudentProfile.objects
        .values("class_name")
        .distinct()
        .count()
    )

    total_subjects = Subject.objects.count()

    total_exams = (
        MarkRecord.objects
        .values("exam_name")
        .distinct()
        .count()
    )

    total_marks_records = MarkRecord.objects.count()
    total_promotions = PromotionRecord.objects.count()

    # -------------------------------
    # Overall Average
    # -------------------------------
    totals = MarkRecord.objects.aggregate(
        total_obtained=Sum("marks_obtained"),
        total_max=Sum("total_marks")
    )

    total_obtained = totals["total_obtained"] or 0
    total_max = totals["total_max"] or 0

    overall_percentage = 0
    if total_max > 0:
        overall_percentage = round(
            (total_obtained / total_max) * 100, 2
        )

    # -------------------------------
    # Exam-wise Performance
    # -------------------------------
    exam_performance = (
        MarkRecord.objects
        .values("exam_name")
        .annotate(
            total_obtained=Sum("marks_obtained"),
            total_max=Sum("total_marks")
        )
        .order_by("exam_name")
    )

    exam_labels = []
    exam_percentages = []

    for exam in exam_performance:
        obtained = exam["total_obtained"] or 0
        maximum = exam["total_max"] or 0

        percentage = 0
        if maximum > 0:
            percentage = round((obtained / maximum) * 100, 2)

        exam_labels.append(exam["exam_name"])
        exam_percentages.append(percentage)

    # -------------------------------
    # Class-wise Performance (NEW)
    # -------------------------------
    class_performance = (
        MarkRecord.objects
        .values("student__studentprofile__class_name")
        .annotate(
            total_obtained=Sum("marks_obtained"),
            total_max=Sum("total_marks")
        )
        .order_by("student__studentprofile__class_name")
    )

    class_labels = []
    class_percentages = []

    for cls in class_performance:
        obtained = cls["total_obtained"] or 0
        maximum = cls["total_max"] or 0

        percentage = 0
        if maximum > 0:
            percentage = round((obtained / maximum) * 100, 2)

        class_name = cls["student__studentprofile__class_name"]

        class_labels.append(class_name)
        class_percentages.append(percentage)

    # -------------------------------
    # Dropdown Data
    # -------------------------------
    class_list = (
        StudentProfile.objects
        .values_list("class_name", flat=True)
        .distinct()
        .order_by("class_name")
    )

    exam_list = (
        MarkRecord.objects
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("exam_name")
    )

    selected_class = request.GET.get("class")
    selected_exam = request.GET.get("exam")

    # -------------------------------
    # Topper Call
    # -------------------------------
    topper = None
    if selected_class and selected_exam:
        topper = get_class_topper(selected_class, selected_exam)

    # -------------------------------
    # Recent Activity Logs
    # -------------------------------
    recent_activities = (
        ActivityLog.objects
        .select_related("user")
        .order_by("-timestamp")[:5]
    )

    # -------------------------------
    # Context
    # -------------------------------
    context = {
        "total_students": total_students,
        "total_classes": total_classes,
        "total_subjects": total_subjects,
        "total_exams": total_exams,
        "total_marks_records": total_marks_records,
        "total_promotions": total_promotions,
        "overall_percentage": overall_percentage,

        "exam_labels": exam_labels,
        "exam_percentages": exam_percentages,

        "class_labels": class_labels,               # NEW
        "class_percentages": class_percentages,     # NEW

        "topper": topper,
        "class_list": class_list,
        "exam_list": exam_list,
        "selected_class": selected_class,
        "selected_exam": selected_exam,

        "recent_activities": recent_activities,
    }

    return render(request, "dashboard/admin.html", context)

@role_required("ADMIN")
def class_overview(request):

    classes = StudentProfile.objects.values_list('class_name', flat=True).distinct()

    class_data = []

    for class_name in classes:

        students = StudentProfile.objects.filter(class_name=class_name)

        ranking_list = []
        total_class_percentage = 0
        valid_students_count = 0

        for student in students:

            marks = MarkRecord.objects.filter(student=student)

            total_obtained = marks.aggregate(total=Sum('marks_obtained'))['total'] or 0
            total_max = marks.aggregate(total=Sum('total_marks'))['total'] or 0

            if total_max > 0:
                percentage = (total_obtained / total_max) * 100
                valid_students_count += 1
                total_class_percentage += percentage
            else:
                percentage = 0

            # Grade Logic (Locked Rule)
            if percentage >= 90:
                grade = 'A+'
            elif percentage >= 75:
                grade = 'A'
            elif percentage >= 60:
                grade = 'B'
            elif percentage >= 40:
                grade = 'C'
            else:
                grade = 'F'

            ranking_list.append({
                'student': student,
                'percentage': round(percentage, 2),
                'grade': grade
            })

        # Sort for Ranking
        ranking_list.sort(key=lambda x: x['percentage'], reverse=True)

        # Assign Rank
        for index, item in enumerate(ranking_list, start=1):
            item['rank'] = index

        # Class Average
        if valid_students_count > 0:
            class_average = total_class_percentage / valid_students_count
        else:
            class_average = 0

        # Topper
        topper = ranking_list[0] if ranking_list else None

        exam_list = MarkRecord.objects.filter(
        student__class_name=class_name
        ).values_list('exam_name', flat=True).distinct()


        class_data.append({
            'class_name': class_name,
            'total_students': students.count(),
            'class_average': round(class_average, 2),
            'topper': topper,
            'ranking_list': ranking_list,
            'exam_list': exam_list   
        })

    context = {
        'class_data': class_data
    }

    return render(request, 'dashboard/class_overview.html', context)

@role_required("ADMIN")
def system_performance(request):

    records = MarkRecord.objects.all()

    total_obtained = sum(r.marks_obtained for r in records)
    total_max = sum(r.total_marks for r in records)

    overall_percentage = 0

    if total_max > 0:
        overall_percentage = round(
            (total_obtained / total_max) * 100, 2
        )

    context = {
        "total_obtained": total_obtained,
        "total_max": total_max,
        "overall_percentage": overall_percentage,
    }

    return render(request, "dashboard/system_performance.html", context)

@role_required('ADMIN')
def admin_security_dashboard(request):
    now = timezone.now()
    today = now.date()

    # ===============================
    # BASIC SECURITY METRICS (11.7)
    # ===============================

    # Failed login today
    failed_today = ActivityLog.objects.filter(
        action_type='FAILED_LOGIN',
        timestamp__date=today
    ).count()

    # Top attacking IP (all-time)
    top_ip = (
        ActivityLog.objects.filter(action_type='FAILED_LOGIN')
        .values('ip_address')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )

    # Failed attempts in last 15 minutes
    last_15_min = now - timedelta(minutes=15)

    recent_failed = ActivityLog.objects.filter(
        action_type='FAILED_LOGIN',
        timestamp__gte=last_15_min
    ).count()

    # ===============================
    # VISUAL ANALYTICS ENGINE (11.8)
    # ===============================

    # 1️⃣ Last 7 Days Failed Login Trend
    seven_days_ago = now - timedelta(days=7)

    daily_trend = (
        ActivityLog.objects.filter(
            action_type='FAILED_LOGIN',
            timestamp__gte=seven_days_ago
        )
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    trend_labels = [str(item['day']) for item in daily_trend]
    trend_counts = [item['count'] for item in daily_trend]

    # 2️⃣ Hour-wise Distribution (Today)
    hourly_data = (
        ActivityLog.objects.filter(
            action_type='FAILED_LOGIN',
            timestamp__date=today
        )
        .annotate(hour=ExtractHour('timestamp'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    hour_labels = [str(item['hour']) for item in hourly_data]
    hour_counts = [item['count'] for item in hourly_data]

    # 3️⃣ Top 5 Attacking IPs
    top_ips = (
        ActivityLog.objects.filter(action_type='FAILED_LOGIN')
        .values('ip_address')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # ===============================
    # CONTEXT
    # ===============================

    context = {
        # Basic Metrics
        'failed_today': failed_today,
        'top_ip': top_ip,
        'recent_failed': recent_failed,

        # Chart Data (JSON Safe)
        'trend_labels': json.dumps(trend_labels),
        'trend_counts': json.dumps(trend_counts),
        'hour_labels': json.dumps(hour_labels),
        'hour_counts': json.dumps(hour_counts),

        # Table Data
        'top_ips': top_ips,
    }

    return render(request, 'dashboard/admin_security_dashboard.html', context)

@admin_required
def admin_blocked_ips(request):
    """Display all blocked IPs with remaining time"""
    blocked_ips = BlockedIP.objects.all()
    for ip in blocked_ips:
        ip.remaining_time = (ip.unblock_at - timezone.now()).total_seconds()
    return render(request, 'dashboard/admin_blocked_ips.html', {'blocked_ips': blocked_ips})


@admin_required
def unblock_ip(request, block_id):
    """Manual unblock"""
    blocked_entry = get_object_or_404(BlockedIP, id=block_id)
    blocked_entry.delete()  # Safe additive removal
    return redirect('admin_blocked_ips')

@admin_required
def manual_block_ip(request):
    """Admin manually blocks an IP"""
    if request.method == 'POST':
        ip_address = request.POST.get('ip_address')
        duration_minutes = int(request.POST.get('duration', 30))  # default 30 min
        unblock_time = timezone.now() + timedelta(minutes=duration_minutes)

        blocked_ip, created = BlockedIP.objects.update_or_create(
            ip_address=ip_address,
            defaults={'unblock_at': unblock_time}
        )

        messages.success(request, f"IP {ip_address} blocked for {duration_minutes} minutes.")
        return redirect('admin_blocked_ips')

    return render(request, 'dashboard/manual_block_ip.html')
       
def edit_student(request, student_id):
    student = StudentProfile.objects.get(id=student_id)
    if request.method == "POST":
        data = request.POST
        for field in ['admission_no','roll_no','full_name','class_name','section','father_name','mother_name','mobile_number','dob','gender','address']:
            setattr(student, field, data[field])
        student.save()
        return redirect('admin_dashboard')
    return render(request, 'dashboard/edit_student.html', {'student': student})

def student_list(request):
    students = StudentProfile.objects.all()
    return render(request, 'dashboard/student_list.html', {'students': students})

@login_required
def add_student(request):

    class_choices = [str(i) for i in range(1, 13)]
    section_choices = ['jasmine', 'lotus', 'lily', 'rose']

    roman_to_number = {
        "I": "1", "II": "2", "III": "3", "IV": "4",
        "V": "5", "VI": "6", "VII": "7", "VIII": "8",
        "IX": "9", "X": "10", "XI": "11", "XII": "12",
    }

    if request.method == "POST":

        # -------- Student Data --------
        email = request.POST.get('email')
        password = request.POST.get('password')
        admission_no = request.POST.get('admission_no')
        student_class = request.POST.get('student_class')
        student_section = request.POST.get('student_section')
        dob = request.POST.get('dob')

        # -------- Parent Data --------
        parent_email = request.POST.get('parent_email')
        parent_password = request.POST.get('parent_password')
        parent_phone = request.POST.get('parent_contact')
        parent_address = request.POST.get('address')

        # -------- Convert Roman to Number --------
        student_class = roman_to_number.get(student_class, student_class)

        # -------- Basic Validation --------
        if not all([
            email, password,
            admission_no,
            student_class,
            student_section,
            parent_email,
            parent_password
        ]):
            messages.error(request, "Please fill all required fields.")
            return redirect('add_student')

        # -------- Class Validation --------
        if student_class not in class_choices:
            messages.error(request, "Invalid class selected.")
            return redirect('add_student')

        if student_section not in section_choices:
            messages.error(request, "Invalid section selected.")
            return redirect('add_student')

        # -------- Duplicate Checks --------
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Student email already exists!")
            return redirect('add_student')

        if CustomUser.objects.filter(email=parent_email).exists():
            messages.error(request, "Parent email already exists!")
            return redirect('add_student')

        if StudentProfile.objects.filter(admission_no=admission_no).exists():
            messages.error(request, "Admission number already exists!")
            return redirect('add_student')

        if email == parent_email:
            messages.error(request, "Student and Parent email cannot be same!")
            return redirect('add_student')

        # -------- Transaction Safe Creation --------
        try:
            with transaction.atomic():

                # Create Student User
                student_user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    role='STUDENT'
                )

                # Create Student Profile
                student_profile = StudentProfile.objects.create(
                    user=student_user,
                    admission_no=admission_no,
                    class_name=student_class,
                    section=student_section,
                    date_of_birth=dob
                )

                # Create Parent User
                parent_user = CustomUser.objects.create_user(
                    email=parent_email,
                    password=parent_password,
                    role='PARENT'
                )

                # Create Parent Profile
                parent_profile = ParentProfile.objects.create(
                    user=parent_user,
                    phone=parent_phone,
                    address=parent_address
                )

                # Link Parent to Student
                parent_profile.students.add(student_profile)

            messages.success(request, "Student Added Successfully!")
            return redirect('add_student')

        except Exception as e:
            print("Error:", e)
            messages.error(request, "Something went wrong. Please try again.")

    context = {
        'class_choices': class_choices,
        'section_choices': section_choices
    }

    return render(request, 'dashboard/add_student.html', context)