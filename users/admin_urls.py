from django.urls import path
from . import admin_views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', admin_views.admin_dashboard, name='dashboard'),
    
    # Players management
    path('players/', admin_views.admin_players, name='players'),
    
    # Registrations management
    path('registrations/', admin_views.admin_registrations, name='registrations'),
    path('registrations/<int:registration_id>/approve/', admin_views.admin_approve_registration, name='approve_registration'),
    path('registrations/<int:registration_id>/reject/', admin_views.admin_reject_registration, name='reject_registration'),
    
    # --- RUTAS DE FINANZAS MODIFICADAS ---
    path('finances/', admin_views.admin_finances, name='finances_dashboard'), # Vista principal de finanzas
    path('finances/definitions/', admin_views.manage_fee_definitions, name='manage_fees'), # (Parte A)
    path('finances/definitions/edit/<int:pk>/', admin_views.edit_fee_definition, name='edit_fee'),
    path('finances/definitions/delete/<int:pk>/', admin_views.delete_fee_definition, name='delete_fee'),
    path('finances/pending/', admin_views.manage_pending_payments, name='manage_pending_payments'), # (Parte B)
    path('finances/review/<int:pk>/', admin_views.review_payment, name='review_payment'),
    path('finances/add/', admin_views.add_transaction, name='add_transaction'), # <-- AÑADIR ESTA LÍNEA
    path('finances/approve/<int:pk>/', admin_views.approve_payment, name='approve_payment'),
    path('finances/reject/<int:pk>/', admin_views.reject_payment, name='reject_payment'),
    # --- FIN RUTAS FINANZAS ---
    
    # Communications
    path('communications/', admin_views.admin_communications, name='communications'),
    path('communications/send-notification/', admin_views.admin_send_notification, name='send_notification'),
    path('communications/<int:pk>/status/', admin_views.communication_status, name='communication_status'),
    
    
    # Sponsors management
    path('sponsors/', admin_views.admin_sponsors, name='admin_sponsors'),
    
    # --- AÑADIR ESTA LÍNEA ---
    path('players/<int:pk>/', admin_views.admin_player_detail, name='admin_player_detail'),
    path('player-cards/', admin_views.admin_player_cards, name='admin_player_cards'),
    path('players/<int:pk>/edit/', admin_views.admin_edit_player, name='admin_player_edit'),
    path('players/<int:player_pk>/add_document/', admin_views.admin_add_player_document, name='admin_add_player_document'),
    # --- FIN ---
    

    # --- AÑADIR ESTAS LÍNEAS ---
    path('categories/', admin_views.manage_categories, name='manage_categories'),
    path('categories/toggle/<int:pk>/', admin_views.toggle_category_registration, name='toggle_category_registration'),
    # --- FIN ---
# --- AÑADIR ESTA LÍNEA ---
    path('finances/assign/', admin_views.assign_fees_to_category, name='assign_fees'),
    # --- FIN ---
    # --- AÑADIR ESTAS LÍNEAS ---
    # Ticket/Solicitudes Management
    path('tickets/', admin_views.list_admin_tickets, name='admin_tickets_list'),
    path('tickets/<int:pk>/', admin_views.view_admin_ticket, name='admin_ticket_view'),
    path('tickets/<int:pk>/close/', admin_views.close_admin_ticket, name='admin_ticket_close'),
    # --- FIN ---
    # --- FIN ---
    # Landing Page Management
    path('landing/news/', admin_views.manage_landing_news, name='manage_news'),
    path('landing/news/edit/<int:pk>/', admin_views.edit_landing_news, name='edit_news'),
    path('landing/news/delete/<int:pk>/', admin_views.delete_landing_news, name='delete_news'),
    path('landing/calendar/', admin_views.manage_landing_calendar, name='manage_calendar'),
    path('landing/calendar/edit/<int:pk>/', admin_views.edit_landing_event, name='edit_event'),
    path('landing/calendar/delete/<int:pk>/', admin_views.delete_landing_event, name='delete_event'),
    path('landing/featured-players/', admin_views.manage_featured_players, name='manage_featured_players'),
]