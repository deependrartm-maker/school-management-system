from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Homework(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='homeworks_created')
    class_name = models.CharField(max_length=50)  # Class for which homework is assigned
    subject = models.CharField(max_length=100)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.class_name}"

class Submission(models.Model):
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    submitted_file = models.FileField(upload_to='homework_submissions/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.homework.title}"