from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('acerca/', views.about_view, name='about'),
    path('equipos/', views.teams_view, name='teams'),
    path('calendario/', views.schedule_view, name='schedule'),
    path('patrocinadores/', views.sponsors_view, name='sponsors'),
    path('contacto/', views.contact_view, name='contact'),
]
