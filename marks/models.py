from django.db import models
from django.core.exceptions import ValidationError
from profiles.models import StudentProfile
from accounts.models import CustomUser


# ==============================
# SUBJECT MODEL
# ==============================

class Subject(models.Model):
    name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=20)

    class Meta:
        unique_together = ("name", "class_name")
        ordering = ["class_name", "name"]

    def __str__(self):
        return f"{self.name} ({self.class_name})"


# ==============================
# MARK RECORD MODEL
# ==============================

class MarkRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_name = models.CharField(max_length=100)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2)
    entered_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam_name')
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["subject"]),
            models.Index(fields=["exam_name"]),
        ]
        ordering = ["student", "subject"]

    def clean(self):
        if self.marks_obtained > self.total_marks:
            raise ValidationError("Marks obtained cannot be greater than total marks.")

    def __str__(self):
        return f"{self.student.admission_no} - {self.subject.name} ({self.exam_name})"


# ==============================
# RESULT LOCK (CLASS-WISE)
# ==============================

class ResultLock(models.Model):
    class_name = models.CharField(max_length=100)
    exam_name = models.CharField(max_length=100)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    locked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('class_name', 'exam_name')
        indexes = [
            models.Index(fields=["class_name"]),
            models.Index(fields=["exam_name"]),
        ]

    def __str__(self):
        status = "Locked" if self.is_locked else "Open"
        return f"{self.class_name} - {self.exam_name} - {status}"


# ==============================
# PROMOTION RECORD (IMMUTABLE)
# ==============================

class PromotionRecord(models.Model):

    STATUS_CHOICES = [
        ("PROMOTED", "Promoted"),
        ("DETAINED", "Detained"),
        ("REEXAM", "Re-Exam"),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE
    )

    class_name = models.CharField(max_length=50)
    exam_name = models.CharField(max_length=100)
    total_percentage = models.FloatField()
    final_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    promoted_to_class = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    generated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True
    )

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "exam_name")
        indexes = [
            models.Index(fields=["exam_name"]),
            models.Index(fields=["class_name"]),
        ]

    # 🔒 IMMUTABLE RECORD
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("PromotionRecord is immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.admission_no} - {self.final_status} ({self.exam_name})"