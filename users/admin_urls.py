from django.urls import path
from . import admin_views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', admin_views.admin_dashboard, name='dashboard'),
    
    # Players management
    path('players/', admin_views.admin_players, name='players'),
    path('players/add/', admin_views.admin_add_player, name='admin_add_player'),
    path('players/edit/<int:player_id>/', admin_views.admin_edit_player, name='admin_edit_player'),
    path('players/delete/<int:player_id>/', admin_views.admin_delete_player, name='admin_delete_player'),
    
    # Registrations management
    path('registrations/', admin_views.admin_registrations, name='registrations'),
    path('registrations/<int:registration_id>/approve/', admin_views.admin_approve_registration, name='approve_registration'),
    path('registrations/<int:registration_id>/reject/', admin_views.admin_reject_registration, name='reject_registration'),
    
    
    # Finances
    path('finances/', admin_views.admin_finances, name='finances'),
    path('finances/add/', admin_views.admin_add_transaction, name='admin_add_transaction'), # <-- NUEVA RUTA

    
    # Communications
    path('communications/', admin_views.admin_communications, name='communications'),
    path('communications/send-notification/', admin_views.admin_send_notification, name='send_notification'),
    
    # Sponsors management
    path('sponsors/', admin_views.admin_sponsors, name='admin_sponsors'),
    
    # Player cards by category
    path('player-cards/', admin_views.admin_player_cards, name='admin_player_cards'),
]