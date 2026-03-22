from django import forms
from .models import HomeworkSubmission

class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['file']