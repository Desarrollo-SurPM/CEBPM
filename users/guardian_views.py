from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from .models import User, GuardianProfile, Registration
from players.models import Category, Player, GuardianPlayer
from finance.models import Payment, Invoice
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient

def is_guardian(user):
    """Verificar si el usuario es un apoderado"""
    if not user.is_authenticated:
        return False
    try:
        user.guardian_profile
        return True
    except GuardianProfile.DoesNotExist:
        return False

@login_required
def guardian_dashboard(request):
    """Dashboard principal para apoderados"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    
    total_players = players.count()
    active_players = players.filter(status='active').count()
    
    pending_payments_agg = Invoice.objects.filter(
        player__in=players,
        status__in=['pendiente', 'atrasada']
    ).aggregate(total=Sum('amount'))
    pending_payments = pending_payments_agg['total'] or 0
    
    today = timezone.now().date()
    player_categories = players.values_list('category', flat=True)
    upcoming_matches = Match.objects.filter(
        category__id__in=player_categories,
        starts_at__gte=today
    ).order_by('starts_at')[:5]
    
    upcoming_trainings = Activity.objects.filter(
        starts_at__gte=today
    ).order_by('starts_at')[:5]
    
    unread_messages = EmailRecipient.objects.filter(
        user=request.user,
        status='enviado' # Idealmente, esto debería ser un campo `is_read=False`
    ).count()
    
    recent_payments = Payment.objects.filter(
        invoice__player__in=players,
        status='completado'
    ).order_by('-paid_at')[:5]
    
    context = {
        'players': players,
        'total_players': total_players,
        'active_players': active_players,
        'pending_payments': pending_payments,
        'upcoming_matches': upcoming_matches,
        'upcoming_trainings': upcoming_trainings,
        'unread_messages': unread_messages,
        'recent_payments': recent_payments,
        'today': today,
    }
    
    return render(request, 'guardian/dashboard.html', context)

@login_required
def guardian_players(request):
    """Gestión de jugadores del apoderado"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    categories = Category.objects.all()

    team_filter = request.GET.get('team')
    status_filter = request.GET.get('status')
    
    if team_filter:
        players = players.filter(category__id=team_filter)
    if status_filter:
        players = players.filter(status=status_filter)
    
    paginator = Paginator(players, 10)
    page_number = request.GET.get('page')
    players_page = paginator.get_page(page_number)
    
    context = {
        'players': players_page,
        'team_filter': team_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'guardian/players.html', context)


@login_required
def guardian_payments(request):
    """Historial de pagos del apoderado"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    payments = Payment.objects.filter(invoice__player__in=players)
    
    # Filtros
    status_filter = request.GET.get('status')
    player_filter = request.GET.get('player')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    if player_filter:
        payments = payments.filter(invoice__player_id=player_filter)
    if date_from:
        payments = payments.filter(invoice__due_date__gte=date_from)
    if date_to:
        payments = payments.filter(invoice__due_date__lte=date_to)
    
    # Estadísticas
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = payments.filter(
        status='pending',
        invoice__due_date__lt=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Paginación
    paginator = Paginator(payments.order_by('-created_at'), 15)
    page_number = request.GET.get('page')
    payments_page = paginator.get_page(page_number)
    
    context = {
        'payments': payments_page,
        'players': players,
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'status_filter': status_filter,
        'player_filter': player_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'guardian/payments.html', context)

@login_required
def guardian_schedule(request):
    """Calendario de partidos y entrenamientos del apoderado."""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    player_categories_ids = guardian_players.values_list('player__category__id', flat=True).distinct()

    # **CORRECCIÓN**: Usar 'starts_at' en lugar de 'date' y 'time'
    matches = Match.objects.filter(
        category__id__in=player_categories_ids
    ).order_by('starts_at')

    # Por ahora, las actividades son generales
    trainings = Activity.objects.filter(type='entrenamiento').order_by('starts_at')

    context = {
        'matches': matches,
        'trainings': trainings,
        'teams': Category.objects.filter(id__in=player_categories_ids),
        'today': timezone.now().date(),
        'tomorrow': timezone.now().date() + timedelta(days=1),
    }
    return render(request, 'guardian/schedule.html', context)


@login_required
def guardian_messages(request):
    """Centro de mensajes para apoderados."""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    # La lógica correcta es buscar los 'EmailRecipient' que pertenecen al usuario
    messages_received = EmailRecipient.objects.filter(user=request.user).select_related('bulk_email', 'bulk_email__created_by').order_by('-created_at')

    paginator = Paginator(messages_received, 10)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)

    context = {
        'messages': messages_page,
        'is_paginated': messages_page.has_other_pages(),
        'page_obj': messages_page,
    }
    return render(request, 'guardian/messages.html', context)


@login_required
def message_detail(request, recipient_id):
    """Muestra el detalle de un mensaje y lo marca como leído."""
    recipient_msg = get_object_or_404(EmailRecipient, id=recipient_id, user=request.user)
    
    if not recipient_msg.read_at:
        recipient_msg.read_at = timezone.now()
        recipient_msg.save()

    return JsonResponse({
        'success': True,
        'message': {
            'title': recipient_msg.bulk_email.title,
            'content': recipient_msg.bulk_email.body_html,
            'sender_name': recipient_msg.bulk_email.created_by.get_full_name() or recipient_msg.bulk_email.created_by.username,
            'created_at': recipient_msg.created_at.strftime("%d/%m/%Y %H:%M"),
            'is_read': recipient_msg.read_at is not None,
        }
    })


@login_required
@require_http_methods(["POST"])
def mark_message_as_read(request, recipient_id):
    """Marca un mensaje como leído."""
    recipient_msg = get_object_or_404(EmailRecipient, id=recipient_id, user=request.user)
    if not recipient_msg.read_at:
        recipient_msg.read_at = timezone.now()
        recipient_msg.save()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def mark_all_as_read(request):
    """Marca todos los mensajes del usuario como leídos."""
    updated_count = EmailRecipient.objects.filter(user=request.user, read_at__isnull=True).update(read_at=timezone.now())
    messages.success(request, f'{updated_count} mensajes fueron marcados como leídos.')
    return JsonResponse({'success': True, 'count': updated_count})

@login_required
def guardian_profile(request):
    """Muestra y actualiza el perfil del apoderado."""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    profile = get_object_or_404(GuardianProfile, user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.save()
        
        messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
        return redirect('guardian:profile')
    
    # Creamos un formulario de cambio de contraseña para pasarlo al template
    password_form = PasswordChangeForm(request.user)

    context = {
        'user': request.user,
        'profile': profile,
        'password_form': password_form, # Enviamos el form al template
    }
    return render(request, 'guardian/profile.html', context)

@login_required
@require_http_methods(["POST"])
def change_password(request):
    """Procesa el cambio de contraseña."""
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        # Mantiene al usuario logueado después de cambiar la contraseña
        update_session_auth_hash(request, user)  
        messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
    else:
        for error in form.errors.values():
            messages.error(request, error.as_text())
    return redirect('guardian:profile')

@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    """Actualiza las preferencias de notificación."""
    profile = get_object_or_404(GuardianProfile, user=request.user)
    
    profile.email_notifications = 'email_notifications' in request.POST
    profile.payment_notifications = 'payment_notifications' in request.POST
    profile.schedule_notifications = 'schedule_notifications' in request.POST
    profile.general_notifications = 'general_notifications' in request.POST
    profile.save()
    
    messages.success(request, 'Tus preferencias de notificación han sido actualizadas.')
    return redirect('guardian:profile')

@login_required
@require_http_methods(["POST"])
def register_player(request):
    """Registrar nuevo jugador"""
    if not is_guardian(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        data = json.loads(request.body)
        
        Registration.objects.create(
            guardian=request.user,
            player_first_name=data.get('first_name'),
            player_last_name=data.get('last_name'),
            player_rut=data.get('rut'),
            player_birth_date=data.get('birth_date'),
            team=data.get('team'),
            emergency_contact=data.get('emergency_contact'),
            emergency_phone=data.get('emergency_phone'),
            medical_info=data.get('medical_info', ''),
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Solicitud de inscripción enviada correctamente. Será revisada por el administrador.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def message_detail(request, message_id):
    """Ver detalles de un mensaje"""
    if not is_guardian(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    teams = [p.category for p in players]
    
    message = get_object_or_404(BulkEmail, 
        id=message_id,
        status='sent'
    )
    
    # Verificar que el apoderado puede ver este mensaje
    can_view = (
        message.audience == 'all_guardians' or
        (message.audience == 'team_guardians' and message.category in teams) or
        request.user in message.recipients.all()
    )
    
    if not can_view:
        return JsonResponse({'success': False, 'error': 'Sin permisos para ver este mensaje'})
    
    # Marcar como leído
    EmailRecipient.objects.get_or_create(
        email=message,
        user=request.user,
        defaults={'read_at': timezone.now()}
    )
    
    return JsonResponse({
        'success': True,
        'html': render(request, 'guardian/message_detail.html', {'message': message}).content.decode()
    })

@login_required
def payment_detail(request, payment_id):
    """Ver detalles de un pago"""
    if not is_guardian(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    player_ids = guardian_players.values_list('player_id', flat=True)
    payment = get_object_or_404(Payment, 
        id=payment_id,
        player_id__in=player_ids
    )
    
    return JsonResponse({
        'success': True,
        'html': render(request, 'guardian/payment_detail.html', {'payment': payment}).content.decode()
    })


@login_required
def guardian_player_detail(request, player_id):
    """Vista detallada de la ficha del jugador"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    # Verificar que el jugador pertenece al apoderado
    guardian_player = get_object_or_404(GuardianPlayer, guardian=request.user, player_id=player_id)
    player = guardian_player.player
    
    # Obtener pagos del jugador
    from finance.models import Invoice
    invoices = Invoice.objects.filter(player=player).order_by('-due_date')
    
    # Estadísticas de pagos
    paid_invoices = invoices.filter(status='pagada')
    pending_invoices = invoices.filter(status='pendiente')
    overdue_invoices = invoices.filter(status='atrasada')
    
    total_paid = paid_invoices.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = pending_invoices.aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = overdue_invoices.aggregate(total=Sum('amount'))['total'] or 0
    
    # Próximos partidos
    upcoming_matches = Match.objects.filter(
        category=player.category,
        starts_at__gte=timezone.now()
    ).order_by('starts_at')[:5]
    
    # Entrenamientos próximos (si existe el modelo)
    upcoming_trainings = []
    
    context = {
        'player': player,
        'invoices': invoices[:10],  # Últimas 10 facturas
        'paid_invoices_count': paid_invoices.count(),
        'pending_invoices_count': pending_invoices.count(),
        'overdue_invoices_count': overdue_invoices.count(),
        'total_paid': total_paid,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'upcoming_matches': upcoming_matches,
        'upcoming_trainings': upcoming_trainings,
    }
    
    return render(request, 'guardian/player_detail.html', context)


@login_required
def guardian_quotas_paid(request):
    """Vista de cuotas pagadas del apoderado"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    # Obtener jugadores del apoderado
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    
    # Filtros
    player_filter = request.GET.get('player')
    year_filter = request.GET.get('year')
    
    from finance.models import Invoice
    paid_invoices = Invoice.objects.filter(
        player__in=players,
        status='pagada'
    ).select_related('player', 'fee_definition').order_by('-due_date')
    
    if player_filter:
        paid_invoices = paid_invoices.filter(player_id=player_filter)
    
    if year_filter:
        paid_invoices = paid_invoices.filter(due_date__year=year_filter)
    
    # Paginación
    paginator = Paginator(paid_invoices, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Total pagado
    total_paid = paid_invoices.aggregate(total=Sum('amount'))['total'] or 0
    
    # Años disponibles para filtro
    years = paid_invoices.dates('due_date', 'year', order='DESC')
    
    context = {
        'page_obj': page_obj,
        'players': players,
        'player_filter': player_filter,
        'year_filter': year_filter,
        'years': years,
        'total_paid': total_paid,
    }
    
    return render(request, 'guardian/quotas_paid.html', context)


@login_required
def guardian_quotas_upcoming(request):
    """Vista de cuotas próximas a pagar"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    # Obtener jugadores del apoderado
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    
    from finance.models import Invoice
    from datetime import date, timedelta
    
    # Cuotas pendientes y próximas a vencer (próximos 30 días)
    today = date.today()
    next_month = today + timedelta(days=30)
    
    upcoming_invoices = Invoice.objects.filter(
        player__in=players,
        status__in=['pendiente', 'atrasada'],
        due_date__lte=next_month
    ).select_related('player', 'fee_definition').order_by('due_date')
    
    # Separar por urgencia
    overdue_invoices = upcoming_invoices.filter(due_date__lt=today)
    due_soon_invoices = upcoming_invoices.filter(
        due_date__gte=today,
        due_date__lte=today + timedelta(days=7)
    )
    pending_invoices = upcoming_invoices.filter(
        due_date__gt=today + timedelta(days=7)
    )
    
    # Totales
    total_overdue = overdue_invoices.aggregate(total=Sum('amount'))['total'] or 0
    total_due_soon = due_soon_invoices.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = pending_invoices.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'overdue_invoices': overdue_invoices,
        'due_soon_invoices': due_soon_invoices,
        'pending_invoices': pending_invoices,
        'total_overdue': total_overdue,
        'total_due_soon': total_due_soon,
        'total_pending': total_pending,
        'total_all': total_overdue + total_due_soon + total_pending,
    }
    
    return render(request, 'guardian/quotas_upcoming.html', context)

@login_required
def guardian_pay_quota(request, invoice_id):
    """Vista para pagar una cuota específica"""
    try:
        guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
        player_ids = guardian_players.values_list('player_id', flat=True)
        invoice = Invoice.objects.get(id=invoice_id, player_id__in=player_ids)
        
        if invoice.status == 'pagada':
            messages.warning(request, 'Esta cuota ya ha sido pagada.')
            return redirect('guardian:guardian_quotas_paid')
        
        if request.method == 'POST':
            payment_method = request.POST.get('payment_method')
            reference_number = request.POST.get('reference_number', '')
            
            # Crear el pago
            payment = Payment.objects.create(
                invoice=invoice,
                amount=invoice.amount,
                method=payment_method,
                status='completado',
                reference_number=reference_number
            )
            
            # Actualizar el estado de la factura
            invoice.status = 'pagada'
            invoice.save()
            
            messages.success(request, f'Pago de ${invoice.amount:,.0f} realizado exitosamente.')
            return redirect('guardian:guardian_quotas_paid')
        
        context = {
            'invoice': invoice,
            'player': invoice.player,
        }
        
        return render(request, 'guardian/pay_quota.html', context)
        
    except Invoice.DoesNotExist:
        messages.error(request, 'La cuota solicitada no existe o no tienes permisos para acceder a ella.')
        return redirect('guardian:guardian_quotas_upcoming')

@login_required
def guardian_pay_multiple(request):
    """Vista para pagar múltiples cuotas"""
    if request.method == 'GET':
        invoice_ids = request.GET.get('invoices', '').split(',')
        invoice_ids = [id for id in invoice_ids if id.isdigit()]
        
        if not invoice_ids:
            messages.error(request, 'No se seleccionaron cuotas para pagar.')
            return redirect('guardian:guardian_quotas_upcoming')
        
        guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
        player_ids = guardian_players.values_list('player_id', flat=True)
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            player_id__in=player_ids,
            status='pendiente'
        )
        
        if not invoices.exists():
            messages.error(request, 'No se encontraron cuotas válidas para pagar.')
            return redirect('guardian:guardian_quotas_upcoming')
        
        total_amount = invoices.aggregate(total=Sum('amount'))['total'] or 0
        
        context = {
            'invoices': invoices,
            'total_amount': total_amount,
        }
        
        return render(request, 'guardian/pay_multiple.html', context)
    
    elif request.method == 'POST':
        invoice_ids = request.POST.getlist('invoice_ids')
        payment_method = request.POST.get('payment_method')
        reference_number = request.POST.get('reference_number', '')
        
        guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
        player_ids = guardian_players.values_list('player_id', flat=True)
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            player_id__in=player_ids,
            status='pendiente'
        )
        
        if not invoices.exists():
            messages.error(request, 'No se encontraron cuotas válidas para pagar.')
            return redirect('guardian:guardian_quotas_upcoming')
        
        total_amount = 0
        payments_created = 0
        
        for invoice in invoices:
            # Crear el pago
            payment = Payment.objects.create(
                invoice=invoice,
                amount=invoice.amount,
                method=payment_method,
                status='completado',
                reference_number=f"{reference_number}-{invoice.id}" if reference_number else ''
            )
            
            # Actualizar el estado de la factura
            invoice.status = 'pagada'
            invoice.save()
            
            total_amount += invoice.amount
            payments_created += 1
        
        messages.success(request, f'Se procesaron {payments_created} pagos por un total de ${total_amount:,.0f}.')
        return redirect('guardian:guardian_quotas_paid')
    
    return redirect('guardian:guardian_quotas_upcoming')