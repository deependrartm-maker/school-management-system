from django.urls import path
from . import views
from .views import *
app_name = "marks"
urlpatterns = [
    path("enter/", views.enter_marks, name="enter_marks"),
    path("marks/<int:student_id>/", views.view_marks, name="view_marks"),
    path("marks/<int:student_id>/print/", views.print_marksheet, name="print_marksheet"),
    path("marks/<int:student_id>/summary/", views.overall_result_summary, name="overall_result_summary"),
    path("marks/<int:student_id>/pdf/", views.generate_marksheet_pdf, name='generate_marksheet_pdf'),
    path("professional-print/<int:student_id>/<str:exam_name>/", views.print_professional_marksheet, name='professional_print'),
    path("merit-list/", views.merit_list_view, name="merit_list"),
    path("generate-promotion/", views.generate_promotion_view, name="generate_promotion"),
    path("promotion-list/", views.promotion_list_view, name="promotion_list"),
    path("print/<int:student_id>/", views.print_result, name="print_result"),
    path("consolidated-print/", views.consolidated_print_view, name="consolidated_print"),
    path('toggle-result-lock/', views.toggle_result_lock, name='toggle_result_lock'),
]