from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import StudentProfile, ParentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("id","user", "admission_no", "class_name", "section")

    def save_model(self, request, obj, form, change):
        if obj.user.role != "STUDENT":
            raise ValidationError(
                "Only users with STUDENT role can have a StudentProfile."
            )
        super().save_model(request, obj, form, change)


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    filter_horizontal = ("students",)

    def save_model(self, request, obj, form, change):
        if obj.user.role != "PARENT":
            raise ValidationError(
                "Only users with PARENT role can have a ParentProfile."
            )
        super().save_model(request, obj, form, change)