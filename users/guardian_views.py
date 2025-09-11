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

from .models import User, GuardianProfile
from players.models import Player, GuardianPlayer
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
        return redirect('pages:home')
    
    # Obtener jugadores del apoderado
    players = Player.objects.filter(guardian=request.user)
    
    # Estadísticas generales
    total_players = players.count()
    active_players = players.filter(status='active').count()
    
    # Pagos pendientes
    pending_payments = Payment.objects.filter(
        player__in=players,
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Próximos partidos y entrenamientos
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(
        Q(home_team__in=[p.team for p in players]) | 
        Q(away_team__in=[p.team for p in players]),
        date__gte=today
    ).order_by('date')[:5]
    
    # upcoming_trainings = Training.objects.filter(
    #     team__in=[p.team for p in players],
    #     date__gte=today
    # ).order_by('date')[:5]
    upcoming_trainings = []
    
    # Mensajes no leídos
    # unread_messages = Message.objects.filter(
    #     Q(audience='all_guardians') |
    #     Q(audience='team_guardians', team__in=[p.team for p in players]) |
    #     Q(recipients=request.user),
    #     status='sent'
    # ).exclude(
    #     messageread__user=request.user
    # ).count()
    unread_messages = 0
    
    # Actividad reciente
    recent_payments = Payment.objects.filter(
        player__in=players
    ).order_by('-created_at')[:5]
    
    context = {
        'players': players,
        'total_players': total_players,
        'active_players': active_players,
        'pending_payments': pending_payments,
        'upcoming_matches': upcoming_matches,
        'upcoming_trainings': upcoming_trainings,
        'unread_messages': unread_messages,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'guardian/dashboard.html', context)

@login_required
def guardian_players(request):
    """Gestión de jugadores del apoderado"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:home')
    
    players = Player.objects.filter(guardian=request.user)
    
    # Filtros
    team_filter = request.GET.get('team')
    status_filter = request.GET.get('status')
    
    if team_filter:
        players = players.filter(team=team_filter)
    if status_filter:
        players = players.filter(status=status_filter)
    
    # Paginación
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
        return redirect('pages:home')
    
    players = Player.objects.filter(guardian=request.user)
    payments = Payment.objects.filter(player__in=players)
    
    # Filtros
    status_filter = request.GET.get('status')
    player_filter = request.GET.get('player')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    if player_filter:
        payments = payments.filter(player_id=player_filter)
    if date_from:
        payments = payments.filter(due_date__gte=date_from)
    if date_to:
        payments = payments.filter(due_date__lte=date_to)
    
    # Estadísticas
    total_paid = payments.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    total_overdue = payments.filter(
        status='pending',
        due_date__lt=timezone.now().date()
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
    """Calendario de partidos y entrenamientos"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:home')
    
    players = Player.objects.filter(guardian=request.user)
    teams = [p.team for p in players]
    
    # Filtros
    team_filter = request.GET.get('team')
    month_filter = request.GET.get('month')
    
    # Partidos
    matches = Match.objects.filter(
        Q(home_team__in=teams) | Q(away_team__in=teams)
    )
    
    # Entrenamientos
    trainings = Training.objects.filter(team__in=teams)
    
    if team_filter:
        matches = matches.filter(
            Q(home_team=team_filter) | Q(away_team=team_filter)
        )
        trainings = trainings.filter(team=team_filter)
    
    if month_filter:
        try:
            year, month = month_filter.split('-')
            matches = matches.filter(date__year=year, date__month=month)
            trainings = trainings.filter(date__year=year, date__month=month)
        except ValueError:
            pass
    
    # Ordenar por fecha
    matches = matches.order_by('date', 'time')
    trainings = trainings.order_by('date', 'time')
    
    context = {
        'matches': matches,
        'trainings': trainings,
        'players': players,
        'teams': list(set(teams)),
        'team_filter': team_filter,
        'month_filter': month_filter,
    }
    
    return render(request, 'guardian/schedule.html', context)

@login_required
def guardian_messages(request):
    """Centro de mensajes para apoderados"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:home')
    
    players = Player.objects.filter(guardian=request.user)
    teams = [p.team for p in players]
    
    # Obtener mensajes dirigidos al apoderado
    messages_query = Message.objects.filter(
        Q(audience='all_guardians') |
        Q(audience='team_guardians', team__in=teams) |
        Q(recipients=request.user),
        status='sent'
    ).distinct()
    
    # Filtros
    type_filter = request.GET.get('type')
    read_filter = request.GET.get('read')
    
    if type_filter:
        messages_query = messages_query.filter(type=type_filter)
    
    if read_filter == 'unread':
        messages_query = messages_query.exclude(
            messageread__user=request.user
        )
    elif read_filter == 'read':
        messages_query = messages_query.filter(
            messageread__user=request.user
        )
    
    # Paginación
    paginator = Paginator(messages_query.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    # Marcar mensajes como leídos cuando se visualizan
    for message in messages_page:
        MessageRead.objects.get_or_create(
            message=message,
            user=request.user,
            defaults={'read_at': timezone.now()}
        )
    
    context = {
        'messages': messages_page,
        'type_filter': type_filter,
        'read_filter': read_filter,
    }
    
    return render(request, 'guardian/messages.html', context)

@login_required
def guardian_profile(request):
    """Perfil del apoderado"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:home')
    
    if request.method == 'POST':
        # Actualizar perfil
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.address = request.POST.get('address', '')
        
        # Cambiar contraseña si se proporciona
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('guardian:profile')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'guardian/profile.html', context)

@login_required
@require_http_methods(["POST"])
def register_player(request):
    """Registrar nuevo jugador"""
    if not is_guardian(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        data = json.loads(request.body)
        
        # Crear registro de inscripción
        registration = Registration.objects.create(
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
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def message_detail(request, message_id):
    """Ver detalles de un mensaje"""
    if not is_guardian(request.user):
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    players = Player.objects.filter(guardian=request.user)
    teams = [p.team for p in players]
    
    message = get_object_or_404(Message, 
        id=message_id,
        status='sent'
    )
    
    # Verificar que el apoderado puede ver este mensaje
    can_view = (
        message.audience == 'all_guardians' or
        (message.audience == 'team_guardians' and message.team in teams) or
        request.user in message.recipients.all()
    )
    
    if not can_view:
        return JsonResponse({'success': False, 'error': 'Sin permisos para ver este mensaje'})
    
    # Marcar como leído
    MessageRead.objects.get_or_create(
        message=message,
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
    
    payment = get_object_or_404(Payment, 
        id=payment_id,
        player__guardian=request.user
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
        return redirect('pages:home')
    
    # Verificar que el jugador pertenece al apoderado
    player = get_object_or_404(Player, id=player_id, guardian=request.user)
    
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
        Q(home_team=player.team) | Q(away_team=player.team),
        date__gte=timezone.now().date()
    ).order_by('date')[:5]
    
    # Entrenamientos próximos (si existe el modelo)
    try:
        from schedules.models import Training
        upcoming_trainings = Training.objects.filter(
            team=player.team,
            date__gte=timezone.now().date()
        ).order_by('date')[:5]
    except ImportError:
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
        return redirect('pages:home')
    
    # Obtener jugadores del apoderado
    players = Player.objects.filter(guardian=request.user)
    
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
        return redirect('pages:home')
    
    # Obtener jugadores del apoderado
    players = Player.objects.filter(guardian=request.user)
    
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
        invoice = Invoice.objects.get(id=invoice_id, guardian=request.user)
        
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
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            guardian=request.user,
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
        
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            guardian=request.user,
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