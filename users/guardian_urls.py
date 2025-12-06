from django.urls import path
from . import guardian_views

app_name = 'guardian'

urlpatterns = [
    # --- Dashboard ---
    path('', guardian_views.guardian_dashboard, name='dashboard'),
    
    # --- Gestión de Jugadores ---
    path('players/', guardian_views.guardian_players, name='players'),
    
    # Esta es la ruta nueva para el botón "Nuevo" del dashboard
    path('players/add/', guardian_views.add_new_player, name='add_new_player'), 
    
    # Esta es la ruta para la API (JSON) de registro si la usas en el frontend
    path('players/api/register/', guardian_views.register_player, name='register_player'),

    path('players/<int:player_id>/', guardian_views.guardian_player_detail, name='guardian_player_detail'),
    path('players/<int:pk>/edit/', guardian_views.guardian_edit_player, name='guardian_player_edit'),
    path('players/<int:player_pk>/add_document/', guardian_views.guardian_add_player_document, name='guardian_add_player_document'),
    
    # --- Pagos y Cuotas ---
    path('payments/', guardian_views.guardian_payments, name='payments'),
    path('payment/<int:payment_id>/', guardian_views.payment_detail, name='payment_detail'),
    
    path('quotas/paid/', guardian_views.guardian_quotas_paid, name='guardian_quotas_paid'),
    path('quotas/upcoming/', guardian_views.guardian_quotas_upcoming, name='guardian_quotas_upcoming'),
    
    path('pay/<int:invoice_id>/', guardian_views.guardian_pay_quota, name='guardian_pay_quota'),
    path('pay/multiple/', guardian_views.guardian_pay_multiple, name='guardian_pay_multiple'),
    
    # --- Calendario ---
    path('schedule/', guardian_views.guardian_schedule, name='schedule'),
    
    # --- Mensajes y Notificaciones ---
    path('messages/', guardian_views.guardian_messages, name='messages'),
    
    # CORRECCIÓN AQUÍ: Cambiamos name='view_message' a 'guardian_view_message' para coincidir con el template
    path('messages/<int:pk>/', guardian_views.guardian_view_message, name='guardian_view_message'),
    
    # Rutas utilitarias / AJAX para mensajes
    path('messages/<int:recipient_id>/detail/', guardian_views.message_detail, name='message_detail'),
    path('messages/<int:recipient_id>/read/', guardian_views.mark_message_as_read, name='mark_message_read'),
    path('messages/read-all/', guardian_views.mark_all_as_read, name='mark_all_messages_read'),
    
    # --- Perfil del Apoderado ---
    path('profile/', guardian_views.guardian_profile, name='profile'),
    path('profile/change-password/', guardian_views.change_password, name='change_password'),
    path('profile/update-notifications/', guardian_views.update_notifications, name='update_notifications'),
]