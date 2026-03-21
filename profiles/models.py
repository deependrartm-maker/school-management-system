from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser


from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    admission_no = models.CharField(max_length=20, unique=True)
    class_name = models.CharField(max_length=20)
    section = models.CharField(max_length=10)
    date_of_birth = models.DateField()

    def clean(self):
        if self.user.role != "STUDENT":
            raise ValidationError(
                "StudentProfile can only be created for users with STUDENT role."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.admission_no}"


class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    students = models.ManyToManyField(
        StudentProfile,
        related_name="parents",
        blank=True
    )

    def clean(self):
        if self.user.role != "PARENT":
            raise ValidationError(
                "ParentProfile can only be created for users with PARENT role."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email