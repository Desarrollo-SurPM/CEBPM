from django.urls import path
from . import views

app_name = 'finance'
urlpatterns = [
    path('report/', views.financial_report_view, name='financial_report'),
]