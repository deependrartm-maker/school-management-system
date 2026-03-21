from profiles.models import StudentProfile
from .models import MarkRecord, ResultLock, PromotionRecord
from django.db.models import Sum


def run_promotion_engine(class_name, exam_name, admin_user):
    # Check if result is locked
    try:
        result_lock = ResultLock.objects.get(
            class_name=class_name,
            exam_name=exam_name,
            is_locked=True
        )
    except ResultLock.DoesNotExist:
        return "Results are not locked. Cannot generate promotion list."

    students = StudentProfile.objects.filter(class_name=class_name)

    for student in students:

        records = MarkRecord.objects.filter(
            student=student,
            exam_name=exam_name
        )

        if not records.exists():
            continue

        total_marks = records.aggregate(total=Sum("total_marks"))["total"] or 0
        obtained_marks = records.aggregate(total=Sum("marks_obtained"))["total"] or 0

        percentage = (obtained_marks / total_marks) * 100 if total_marks > 0 else 0

        fail_count = records.filter(marks_obtained__lt=33).count()

        if fail_count == 0 and percentage >= 33:
            status = "PROMOTED"
            promoted_to = get_next_class(class_name)

        elif fail_count <= 2:
            status = "REEXAM"
            promoted_to = None

        else:
            status = "DETAINED"
            promoted_to = None

        # Avoid duplicate entry
        if not PromotionRecord.objects.filter(student=student, exam_name=exam_name).exists():
            PromotionRecord.objects.create(
                student=student,
                class_name=class_name,
                exam_name=exam_name,
                total_percentage=round(percentage, 2),
                final_status=status,
                promoted_to_class=promoted_to,
                generated_by=admin_user
            )

    return "Promotion list generated successfully."


def get_next_class(current_class):
    try:
        number = int(current_class)
        return str(number + 1)
    except:
        return None