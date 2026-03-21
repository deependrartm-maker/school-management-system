from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib import messages
from accounts.permissions import can_view_student
from accounts.decorators import role_required
from profiles.models import StudentProfile
from .models import Subject, MarkRecord
from .permissions import can_view_marks
from django.db.models import Sum
from .models import ResultLock
from django.http import HttpResponseForbidden
from audit.utils import log_activity
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.http import HttpResponse
from .professional_pdf_engine import generate_professional_marksheet_pdf
from django.utils import timezone
from io import BytesIO
from .grade_utils import calculate_pass_fail, calculate_division, calculate_class_ranks
from django.shortcuts import render
from .promotion_engine import run_promotion_engine
from django.contrib.admin.views.decorators import staff_member_required
from .models import PromotionRecord
# ==============================================
# ENTER MARKS (TEACHER ONLY)
# ==============================================

@login_required
@role_required('TEACHER')
def enter_marks(request):

    exam = request.GET.get("exam")
    class_name = request.GET.get("class_name")
    section = request.GET.get("section")

    students = None
    subjects = None

    # ===============================
    # CLASS ROMAN → NUMBER MAP
    # ===============================
    CLASS_MAP = {
        "I": "1",
        "II": "2",
        "III": "3",
        "IV": "4",
        "V": "5",
        "VI": "6",
        "VII": "7",
        "VIII": "8",
        "IX": "9",
        "X": "10",
        "XI": "11",
        "XII": "12"
    }

    # ===============================
    # SECTION FLOWER → LETTER MAP
    # ===============================
    SECTION_MAP = {
        "Jasmine": "A",
        "Lotus": "B",
        "Lily": "C",
        "Rose": "D"
    }

    # ===============================
    # LOAD STUDENTS (GET REQUEST)
    # ===============================
    if exam and class_name and section:

        # ❌ Skip Board Classes
        if class_name in ["X", "XII", "10", "12"]:
            messages.error(request, "Board classes not allowed here.")
        else:

            # 🔹 Convert Roman → Number if needed
            db_class = CLASS_MAP.get(class_name, class_name)

            # 🔹 Section flexible matching
            possible_sections = [
                section,                         # As selected
                SECTION_MAP.get(section),        # Flower → Letter
            ]

            students = StudentProfile.objects.filter(
                class_name=db_class,
                section__in=[s for s in possible_sections if s]
            )

            subjects = Subject.objects.filter(class_name=db_class)

    # ===============================
    # SAVE MARKS (POST REQUEST)
    # ===============================
    if request.method == "POST":

        exam = request.POST.get("exam")
        class_name = request.POST.get("class_name")
        section = request.POST.get("section")

        db_class = CLASS_MAP.get(class_name, class_name)

        # 🔒 RESULT LOCK CHECK (Corrected)
        if ResultLock.objects.filter(
            class_name=db_class,
            exam_name=exam,
            is_locked=True
        ).exists():
            return HttpResponseForbidden("Result is locked by Admin.")

        for key in request.POST:
            if key.startswith("project_"):

                student_id = key.split("_")[1]

                try:
                    project = float(request.POST.get(f"project_{student_id}", 0))
                    theory = float(request.POST.get(f"theory_{student_id}", 0))
                except:
                    continue

                # 🔒 Backend Validation
                if not (5 <= project <= 20):
                    continue
                if not (10 <= theory <= 80):
                    continue

                total_marks = 100
                marks_obtained = project + theory

                try:
                    student = StudentProfile.objects.get(id=student_id)

                    MarkRecord.objects.update_or_create(
                        student=student,
                        exam_name=exam,
                        defaults={
                            "marks_obtained": marks_obtained,
                            "total_marks": total_marks,
                            "entered_by": request.user
                        }
                    )

                except Exception as e:
                    print("Error saving marks:", e)
                    continue

        messages.success(request, "Marks saved successfully.")

    # ===============================
    # FINAL RENDER
    # ===============================
    return render(request, "marks/enter.html", {
        "students": students,
        "subjects": subjects,
        "selected_exam": exam,
        "class_name": class_name,
        "section": section
    })

@login_required
def view_marks(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    # Permission Check
    if not can_view_marks(request.user, student):
        return render(request, "403.html", status=403)

    records = MarkRecord.objects.filter(student=student)

    marks_data = []

    for record in records:
        percentage = (record.marks_obtained / record.total_marks) * 100

        # Grade Logic
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 75:
            grade = "A"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "F"

        marks_data.append({
            "subject": record.subject.name,
            "exam": record.exam_name,
            "marks": record.marks_obtained,
            "total": record.total_marks,
            "percentage": round(percentage, 2),
            "grade": grade,
        })

    context = {
        "student": student,
        "marks_data": marks_data,
    }

    return render(request, "marks/view.html", context)

@role_required('ADMIN')
def print_marksheet(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    if not can_view_student(request.user, student):
        return render(request, "403.html", status=403)

    records = MarkRecord.objects.filter(student=student)

    marks_data = []

    for record in records:
        percentage = (record.marks_obtained / record.total_marks) * 100

        if percentage >= 90:
            grade = "A+"
        elif percentage >= 75:
            grade = "A"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "F"

        marks_data.append({
            "subject": record.subject.name,
            "exam_name": record.exam_name,
            "marks_obtained": record.marks_obtained,
            "total_marks": record.total_marks,
            "percentage": round(percentage, 2),
            "grade": grade
        })

    context = {
        "student": student,
        "marks_data": marks_data
    }

    return render(request, "marks/marksheet.html", context)

@login_required
def overall_result_summary(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    if not can_view_student(request.user, student):
        return HttpResponseForbidden("Permission denied.")

    exam_name = "sem1"   # 🔒 FIXED

    if not ResultLock.objects.filter(
        class_name=student.class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists():
        return HttpResponseForbidden("Results not yet published by Admin.")

    marks = MarkRecord.objects.filter(
        student=student,
        exam_name=exam_name
    )

    total_obtained = sum(m.marks_obtained for m in marks)
    total_max = sum(m.total_marks for m in marks)

    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0

    result_status, calculated_percentage = calculate_pass_fail(marks)
    division = calculate_division(calculated_percentage)

    # Rank Calculation
    class_students = StudentProfile.objects.filter(class_name=student.class_name)

    students_data = []
    for s in class_students:
        s_marks = MarkRecord.objects.filter(student=s, exam_name=exam_name)
        _, perc = calculate_pass_fail(s_marks)
        students_data.append({"student_id": s.id, "percentage": perc})

    rank_dict = calculate_class_ranks(students_data)
    student_rank = rank_dict.get(student.id, "N/A")

    context = {
        'student': student,
        'percentage': percentage,
        'total_obtained': total_obtained,
        'total_max': total_max,
        'result_status': result_status,
        'division': division,
        'rank': student_rank,
        'exam_name': exam_name
    }

    return render(request, 'marks/overall_summary.html', context)

@role_required('ADMIN')
def toggle_result_lock(request):

    print("LOCK FUNCTION HIT")

    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        exam_name = request.POST.get('exam_name')

        lock_obj, created = ResultLock.objects.get_or_create(
            class_name=class_name,
            exam_name=exam_name
        )

        lock_obj.is_locked = not lock_obj.is_locked
        lock_obj.locked_by = request.user
        lock_obj.save()

        # ✅ AUDIT LOGGING ADDED (SAFE & ADDITIVE)
        if lock_obj.is_locked:
            log_activity(
                request.user,
                'RESULT_LOCK',
                f"{request.user.email} locked result for {class_name} - {exam_name}",
                request
            )
            messages.success(request, "Result Locked Successfully")
        else:
            log_activity(
                request.user,
                'RESULT_LOCK',
                f"{request.user.email} unlocked result for {class_name} - {exam_name}",
                request
            )
            messages.success(request, "Result Unlocked Successfully")

    return redirect('class_overview')

@login_required
def consolidated_print_view(request):

    if request.user.role != "ADMIN":
        return render(request, "dashboard/403.html")

    class_name = request.GET.get("class")

    if not class_name:
        return HttpResponseForbidden("Class not specified.")

    exam_name = "sem1"  # 🔒 MASTER RULE

    # 🔒 LOCK CHECK (STRICT)
    if not ResultLock.objects.filter(
        class_name=class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists():
        return HttpResponseForbidden("Result not locked yet by Admin.")

    students = StudentProfile.objects.filter(class_name=class_name)

    result_data = []

    for student in students:
        records = MarkRecord.objects.filter(
            student=student,
            exam_name=exam_name
        )

        total_obtained = sum(r.marks_obtained for r in records)
        total_max = sum(r.total_marks for r in records)

        percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0

        # Grade Logic
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 75:
            grade = "A"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 40:
            grade = "C"
        else:
            grade = "F"

        result_data.append({
            "student": student,
            "total_obtained": total_obtained,
            "total_max": total_max,
            "percentage": percentage,
            "grade": grade
        })

    # 🔥 SORT BY PERCENTAGE
    result_data.sort(key=lambda x: x["percentage"], reverse=True)

    # 🔥 RANK WITH TIE HANDLING
    current_rank = 0
    last_percentage = None

    for index, item in enumerate(result_data):
        if item["percentage"] != last_percentage:
            current_rank = index + 1
            last_percentage = item["percentage"]

        item["rank"] = current_rank

    # Class Average
    class_average = round(
        sum(r["percentage"] for r in result_data) / len(result_data),
        2
    ) if result_data else 0

    topper = result_data[0] if result_data else None

    context = {
        "class_name": class_name,
        "results": result_data,
        "class_average": class_average,
        "topper": topper,
        "exam_name": exam_name
    }

    return render(request, "marks/consolidated_print.html", context)

def generate_marksheet_pdf(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)
    exam_name = "sem1"

    if not ResultLock.objects.filter(
        class_name=student.class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists():
        return HttpResponse("Result not locked. PDF not allowed.")

    marks = MarkRecord.objects.filter(
        student=student,
        exam_name=exam_name
    )

    total_obtained = sum(m.marks_obtained for m in marks)
    total_max = sum(m.total_marks for m in marks)

    percentage = round((total_obtained / total_max) * 100, 2) if total_max else 0

    return generate_professional_marksheet_pdf(
        student=student,
        marks=marks,
        exam_name=exam_name
    )

def print_professional_marksheet(request, student_id, exam_name):

    # ---- Get student ----
    student = get_object_or_404(StudentProfile, id=student_id)

    # ---- Check Result Lock ----
    lock_exists = ResultLock.objects.filter(
        class_name=student.class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists()

    if not lock_exists:
        return HttpResponse("Result not locked. Cannot generate professional marksheet.")

    # ---- Get Marks ----
    marks = MarkRecord.objects.filter(
        student=student,
        exam_name=exam_name
    )

    if not marks.exists():
        return HttpResponse("No marks found.")

    # ---- Generate PDF ----
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="professional_marksheet.pdf"'

    generate_professional_marksheet_pdf(student, marks, exam_name, response)

    return response



@login_required
def merit_list_view(request):

    if request.user.role not in ["ADMIN", "TEACHER"]:
        return render(request, "dashboard/403.html")

    class_name = request.GET.get("class_name")
    exam_name = "sem1"   # 🔒 FORCE sem1

    classes = StudentProfile.objects.values_list(
        "class_name", flat=True
    ).distinct()

    students_data = []

    if class_name:

        # 🔒 LOCK CHECK
        if not ResultLock.objects.filter(
            class_name=class_name,
            exam_name=exam_name,
            is_locked=True
        ).exists():
            messages.error(request, "Result not locked yet.")
            return redirect("dashboard")

        students = StudentProfile.objects.filter(class_name=class_name)

        totals = (
            MarkRecord.objects
            .filter(student__in=students, exam_name=exam_name)
            .values("student")
            .annotate(
                total_obtained=Sum("marks_obtained"),
                total_max=Sum("total_marks")
            )
        )

        temp_list = []

        for t in totals:
            student_obj = StudentProfile.objects.get(id=t["student"])

            total = t["total_obtained"] or 0
            total_max = t["total_max"] or 0

            percentage = round((total / total_max) * 100, 2) if total_max else 0

            temp_list.append({
                "student": student_obj,
                "total": total,
                "percentage": percentage
            })

        # 🔥 SORT
        temp_list.sort(key=lambda x: x["percentage"], reverse=True)

        # 🔥 RANK WITH TIE HANDLING
        current_rank = 0
        last_percentage = None

        for index, item in enumerate(temp_list):
            if item["percentage"] != last_percentage:
                current_rank = index + 1
                last_percentage = item["percentage"]

            pass_fail = "PASS" if item["percentage"] >= 40 else "FAIL"
            division = calculate_division(item["percentage"])

            students_data.append({
                "student": item["student"],
                "total": item["total"],
                "percentage": item["percentage"],
                "rank": current_rank,
                "pass_fail": pass_fail,
                "division": division
            })

    context = {
        "classes": classes,
        "students_data": students_data,
        "selected_class": class_name,
        "exam_name": exam_name
    }

    return render(request, "marks/merit_list.html", context)


@staff_member_required
def generate_promotion_view(request):

    message = None

    if request.method == "POST":
        class_name = request.POST.get("class_name")
        exam_name = request.POST.get("exam_name")

        message = run_promotion_engine(
            class_name=class_name,
            exam_name=exam_name,
            admin_user=request.user
        )

    return render(request, "marks/generate_promotion.html", {
        "message": message
    })
from .models import PromotionRecord

def promotion_list_view(request):

    class_name = request.GET.get("class_name")
    exam_name = request.GET.get("exam_name")

    records = PromotionRecord.objects.all()

    if class_name:
        records = records.filter(class_name=class_name)

    if exam_name:
        records = records.filter(exam_name=exam_name)

    return render(request, "marks/promotion_list.html", {
        "records": records
    })

# ==============================================
# STEP 21.3 – MODERN HTML PRINT RESULT
# ==============================================

@login_required
def print_result(request, student_id):

    student = get_object_or_404(StudentProfile, id=student_id)

    exam_name = request.GET.get("exam")

    if not exam_name:
        return HttpResponse("Exam name required in URL (?exam=Final)")

    # 🔒 Result Lock Check
    lock_exists = ResultLock.objects.filter(
        class_name=student.class_name,
        exam_name=exam_name,
        is_locked=True
    ).exists()

    if not lock_exists:
        return HttpResponseForbidden("Result not yet published by Admin.")

    # Fetch Marks
    mark_records = MarkRecord.objects.filter(
        student=student,
        exam_name=exam_name
    )

    if not mark_records.exists():
        return HttpResponse("No marks found for this exam.")

    total_marks = sum(record.total_marks for record in mark_records)
    obtained_marks = sum(record.marks_obtained for record in mark_records)

    percentage = round((obtained_marks / total_marks) * 100, 2) if total_marks else 0

    # Promotion Status
    promotion = PromotionRecord.objects.filter(
        student=student,
        exam_name=exam_name
    ).first()

    promotion_status = promotion.final_status if promotion else "PENDING"

    context = {
        "student": student,
        "mark_records": mark_records,
        "total_marks": total_marks,
        "obtained_marks": obtained_marks,
        "percentage": percentage,
        "promotion_status": promotion_status,
        "exam_name": exam_name,
        "today": timezone.now().date()
    }

    return render(request, "marks/print_result.html", context)

