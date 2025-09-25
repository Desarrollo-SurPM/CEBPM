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
    path('profile/change-password/', guardian_views.change_password, name='change_password'),
    path('profile/update-notifications/', guardian_views.update_notifications, name='update_notifications'),
    # Player detail view
    path('player/<int:player_id>/', guardian_views.guardian_player_detail, name='guardian_player_detail'),
    
    # Quotas management
    path('quotas/paid/', guardian_views.guardian_quotas_paid, name='guardian_quotas_paid'),
    path('quotas/upcoming/', guardian_views.guardian_quotas_upcoming, name='guardian_quotas_upcoming'),
    
    # Payment functionality
    path('pay/<int:invoice_id>/', guardian_views.guardian_pay_quota, name='guardian_pay_quota'),
    path('pay/multiple/', guardian_views.guardian_pay_multiple, name='guardian_pay_multiple'),
    

    # Mensajes (RUTAS CORREGIDAS Y AÑADIDAS)
    path('messages/', guardian_views.guardian_messages, name='messages'),
    path('messages/<int:recipient_id>/detail/', guardian_views.message_detail, name='message_detail'),
    path('messages/<int:recipient_id>/read/', guardian_views.mark_message_as_read, name='mark_message_read'),
    path('messages/read-all/', guardian_views.mark_all_as_read, name='mark_all_messages_read'), # Corregido el nombre
    
]