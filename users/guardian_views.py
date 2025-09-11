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

from .models import User
from players.models import Player, GuardianPlayer
from finance.models import Payment
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient

def is_guardian(user):
    """Verificar si el usuario es un apoderado"""
    return user.is_authenticated and user.user_type == 'guardian'

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
    
    upcoming_trainings = Training.objects.filter(
        team__in=[p.team for p in players],
        date__gte=today
    ).order_by('date')[:5]
    
    # Mensajes no leídos
    unread_messages = Message.objects.filter(
        Q(audience='all_guardians') |
        Q(audience='team_guardians', team__in=[p.team for p in players]) |
        Q(recipients=request.user),
        status='sent'
    ).exclude(
        messageread__user=request.user
    ).count()
    
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