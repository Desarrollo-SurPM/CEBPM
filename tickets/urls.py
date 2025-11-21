from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.list_tickets, name='list'),
    path('crear/', views.create_ticket, name='create'),
    path('<int:pk>/', views.view_ticket, name='view'),
]