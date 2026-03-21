from django.urls import path
from .views import verify_marksheet

urlpatterns = [
    path('<str:token>/', verify_marksheet, name='verify_marksheet'),
]