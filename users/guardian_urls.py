from django.urls import path
from . import guardian_views

app_name = 'guardian'

urlpatterns = [
    # Dashboard principal
    path('', guardian_views.guardian_dashboard, name='dashboard'),
    
    # Gestión de jugadores
    path('players/', guardian_views.guardian_players, name='players'),
    path('register-player/', guardian_views.register_player, name='register_player'),
    
    # Pagos
    path('payments/', guardian_views.guardian_payments, name='payments'),
    path('payment/<int:payment_id>/', guardian_views.payment_detail, name='payment_detail'),
    
    # Calendario
    path('schedule/', guardian_views.guardian_schedule, name='schedule'),
    
    # Mensajes
    path('messages/', guardian_views.guardian_messages, name='messages'),
    path('message/<int:message_id>/', guardian_views.message_detail, name='message_detail'),
    
    # Perfil
    path('profile/', guardian_views.guardian_profile, name='profile'),
]