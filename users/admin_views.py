from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, GuardianProfile, AdminProfile
from players.models import Player, GuardianPlayer
from finance.models import Payment, FeeDefinition, Invoice, Sponsor
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient


def is_admin(user):
    """Check if user is an admin"""
    if not user.is_authenticated:
        return False
    try:
        user.admin_profile
        return True
    except AdminProfile.DoesNotExist:
        return False


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard with overview statistics"""
    # Get statistics
    total_players = Player.objects.count()
    total_guardians = GuardianProfile.objects.count()
    total_payments = Payment.objects.filter(status='completado').count()
    
    # Cuotas statistics
    total_paid_quotas = Invoice.objects.filter(status='pagada').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_pending_quotas = Invoice.objects.filter(status='pendiente').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_overdue_quotas = Invoice.objects.filter(status='atrasada').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Total funds (completed payments)
    total_funds = Payment.objects.filter(status='completado').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Active sponsors count
    active_sponsors = Sponsor.objects.filter(active=True).count()
    
    # Pending registrations (assuming this model exists)
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    
    try:
        from players.models import PlayerRegistration
        pending_registrations = PlayerRegistration.objects.filter(status='pending').count()
        # Recent activities
        recent_registrations = PlayerRegistration.objects.order_by('-created_at')[:5]
        monthly_registrations = PlayerRegistration.objects.filter(
            created_at__gte=current_month
        ).count()
    except ImportError:
        pending_registrations = 0
        recent_registrations = []
        monthly_registrations = 0
    
    recent_payments = Payment.objects.filter(status='completed').order_by('-created_at')[:5]
    upcoming_matches = Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:5]
    monthly_payments = Payment.objects.filter(
        created_at__gte=current_month,
        status='completed'
    ).count()
    
    context = {
        'total_players': total_players,
        'total_guardians': total_guardians,
        'total_payments': total_payments,
        'pending_registrations': pending_registrations,
        'total_paid_quotas': total_paid_quotas,
        'total_pending_quotas': total_pending_quotas,
        'total_overdue_quotas': total_overdue_quotas,
        'total_funds': total_funds,
        'active_sponsors': active_sponsors,
        'recent_registrations': recent_registrations,
        'recent_payments': recent_payments,
        'upcoming_matches': upcoming_matches,
        'monthly_registrations': monthly_registrations,
        'monthly_payments': monthly_payments,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_players(request):
    """Manage players"""
    search_query = request.GET.get('search', '')
    team_filter = request.GET.get('team', '')
    status_filter = request.GET.get('status', '')
    
    players = Player.objects.all()
    
    if search_query:
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(rut__icontains=search_query)
        )
    
    if team_filter:
        players = players.filter(category=team_filter)
    
    if status_filter:
        players = players.filter(status=status_filter)
    
    players = players.order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(players, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique teams for filter
    teams = Player.objects.values_list('category__name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'team_filter': team_filter,
        'status_filter': status_filter,
        'teams': teams,
    }
    
    return render(request, 'admin/players.html', context)


@login_required
@user_passes_test(is_admin)
def admin_registrations(request):
    """Manage player registrations"""
    status_filter = request.GET.get('status', 'pending')
    
    registrations = PlayerRegistration.objects.all()
    
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    registrations = registrations.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(registrations, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/registrations.html', context)


@login_required
@user_passes_test(is_admin)
def admin_approve_registration(request, registration_id):
    """Approve a player registration"""
    if request.method == 'POST':
        registration = get_object_or_404(PlayerRegistration, id=registration_id)
        registration.status = 'approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        # Create player if not exists
        if not registration.player:
            player = Player.objects.create(
                first_name=registration.first_name,
                last_name=registration.last_name,
                rut=registration.rut,
                birthdate=registration.birth_date,
                team=registration.team,
                guardian=registration.guardian,
                status='active'
            )
            registration.player = player
            registration.save()
        
        messages.success(request, f'Registro de {registration.first_name} {registration.last_name} aprobado exitosamente.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_admin)
def admin_reject_registration(request, registration_id):
    """Reject a player registration"""
    if request.method == 'POST':
        registration = get_object_or_404(PlayerRegistration, id=registration_id)
        rejection_reason = request.POST.get('reason', '')
        
        registration.status = 'rejected'
        registration.rejection_reason = rejection_reason
        registration.save()
        
        messages.success(request, f'Registro de {registration.first_name} {registration.last_name} rechazado.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_admin)
def admin_finances(request):
    """Manage finances"""
    # Get payment statistics
    total_income = Payment.objects.filter(status='completed').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    pending_payments = Payment.objects.filter(status='pending').count()
    overdue_payments = Payment.objects.filter(
        status='pending',
        invoice__due_date__lt=timezone.now().date()
    ).count()
    
    # Recent payments
    recent_payments = Payment.objects.order_by('-created_at')[:10]
    
    # Monthly income chart data
    monthly_income = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        income = Payment.objects.filter(
            status='completed',
            created_at__range=[month_start, month_end]
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        monthly_income.append({
            'month': month_start.strftime('%B %Y'),
            'income': float(income)
        })
    
    monthly_income.reverse()
    
    context = {
        'total_income': total_income,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'recent_payments': recent_payments,
        'monthly_income': monthly_income,
    }
    
    return render(request, 'admin/finances.html', context)


@login_required
@user_passes_test(is_admin)
def admin_communications(request):
    """Manage communications"""
    # Get recent notifications and messages
    recent_notifications = Notification.objects.order_by('-created_at')[:10]
    recent_messages = Message.objects.order_by('-created_at')[:10]
    
    context = {
        'recent_notifications': recent_notifications,
        'recent_messages': recent_messages,
    }
    
    return render(request, 'admin/communications.html', context)


@login_required
@user_passes_test(is_admin)
def admin_send_notification(request):
    """Send notification to users"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')
        
        recipients = []
        
        if recipient_type == 'all':
            recipients = User.objects.all()
        elif recipient_type == 'guardians':
            recipients = User.objects.filter(guardianprofile__isnull=False)
        elif recipient_type == 'admins':
            recipients = User.objects.filter(adminprofile__isnull=False)
        
        # Create notifications
        notifications = []
        for user in recipients:
            notifications.append(Notification(
                user=user,
                title=title,
                message=message,
                sender=request.user
            ))
        
        Notification.objects.bulk_create(notifications)
        
        messages.success(request, f'Notificación enviada a {len(recipients)} usuarios.')
        return redirect('admin_communications')
    
    return render(request, 'admin/send_notification.html')


@login_required
@user_passes_test(is_admin)
def admin_sponsors(request):
    """Manage sponsors"""
    sponsors = Sponsor.objects.all().order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        sponsors = sponsors.filter(active=True)
    elif status_filter == 'inactive':
        sponsors = sponsors.filter(active=False)
    
    # Paginación
    paginator = Paginator(sponsors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/sponsors.html', context)


@login_required
@user_passes_test(is_admin)
def admin_player_cards(request):
    """View player cards by category"""
    from players.models import Category
    
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    players = Player.objects.all()
    
    if category_filter:
        players = players.filter(category_id=category_filter)
    
    if search_query:
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(rut__icontains=search_query)
        )
    
    players = players.select_related('category').order_by('category__name', 'last_name')
    
    # Paginación
    paginator = Paginator(players, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorías para filtro
    categories = Category.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/player_cards.html', context)