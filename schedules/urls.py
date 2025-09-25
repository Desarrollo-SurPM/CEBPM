from django.urls import path
from . import views

app_name = 'schedules'
urlpatterns = [
    path('', views.schedule_list_view, name='schedule_list'),
]