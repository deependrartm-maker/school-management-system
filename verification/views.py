import hashlib
from django.conf import settings
from django.shortcuts import render
from marks.models import MarkRecord, ResultLock
from profiles.models import StudentProfile
from marks.grade_utils import calculate_grade
from django.db.models import Sum


def verify_marksheet(request, token):
    context = {
        "valid": False,
        "error": None
    }

    try:
        parts = token.split("_")

        if len(parts) != 3:
            context["error"] = "Invalid token structure."
            return render(request, "verification/verify.html", context)

        admission_no = parts[0]
        exam_name = parts[1]
        received_signature = parts[2]

        # Recreate expected signature
        raw_string = f"{admission_no}:{exam_name}:{settings.SECRET_KEY}"
        expected_signature = hashlib.sha256(raw_string.encode()).hexdigest()

        if received_signature != expected_signature:
            context["error"] = "Document signature mismatch."
            return render(request, "verification/verify.html", context)

        student = StudentProfile.objects.get(admission_no=admission_no)

        marks = MarkRecord.objects.filter(
            student=student,
            exam_name=exam_name
        )

        if not marks.exists():
            context["error"] = "No marks found."
            return render(request, "verification/verify.html", context)

        result_lock = ResultLock.objects.get(
            class_name=student.class_name,
            exam_name=exam_name
        )

        if not result_lock.is_locked:
            context["error"] = "Result not officially locked."
            return render(request, "verification/verify.html", context)

        total_obtained = marks.aggregate(Sum("marks_obtained"))["marks_obtained__sum"]
        total_max = marks.aggregate(Sum("total_marks"))["total_marks__sum"]

        percentage = (total_obtained / total_max) * 100
        grade = calculate_grade(percentage)

        context.update({
            "valid": True,
            "student": student,
            "marks": marks,
            "total_obtained": total_obtained,
            "total_max": total_max,
            "percentage": round(percentage, 2),
            "grade": grade,
            "exam_name": exam_name,
        })

    except Exception:
        context["error"] = "Verification failed."

    return render(request, "verification/verify.html", context)