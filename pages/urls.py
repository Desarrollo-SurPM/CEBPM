from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('acerca/', views.about_view, name='about'),
    path('equipos/', views.teams_view, name='teams'),
    
    # CORRECCIÓN AQUÍ: cambiamos schedule_view por schedule
    path('calendario/', views.schedule, name='schedule'),
    
    path('sponsors/', views.sponsors_view, name='sponsors'),
    path('contacto/', views.contact_view, name='contact'),
]