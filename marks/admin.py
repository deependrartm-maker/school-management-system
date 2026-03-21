from django.contrib import admin
from .models import Subject, MarkRecord
from .models import ResultLock
from .models import PromotionRecord

@admin.register(ResultLock)
class ResultLockAdmin(admin.ModelAdmin):
    list_display = ('class_name', 'exam_name', 'is_locked', 'locked_by', 'locked_at')
    list_filter = ('class_name', 'exam_name', 'is_locked')


admin.site.register(Subject)
admin.site.register(MarkRecord)
admin.site.register(PromotionRecord)