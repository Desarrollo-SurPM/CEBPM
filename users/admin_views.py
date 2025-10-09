from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db import models
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, GuardianProfile, AdminProfile, Registration
from players.models import Player, GuardianPlayer, Category
from finance.models import Payment, FeeDefinition, Invoice
from sponsors.models import Sponsor
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient
from players.forms import PlayerForm # <-- Importado


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
    # ... (código existente sin cambios) ...
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
    
    # Pending registrations
    pending_registrations = Registration.objects.filter(status='pending').count()
    
    # Monthly statistics
    current_month = timezone.now().replace(day=1)
    monthly_registrations = Registration.objects.filter(
        created_at__gte=current_month
    ).count()
    monthly_payments = Payment.objects.filter(
        created_at__gte=current_month,
        status='completado'
    ).count()

    # Recent activities
    recent_registrations = Registration.objects.order_by('-created_at')[:5]
    recent_payments = Payment.objects.filter(status='completado').order_by('-created_at')[:5]
    upcoming_matches = Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:5]
    
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

# ... (código existente sin cambios hasta admin_players) ...
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
            Q(last_name__icontains=search_query)
        )
    
    if team_filter:
        players = players.filter(category__name=team_filter)
    
    if status_filter:
        players = players.filter(is_active=(status_filter == 'active'))
    
    players = players.order_by('last_name', 'first_name')
    
    paginator = Paginator(players, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    teams = Category.objects.values_list('name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'team_filter': team_filter,
        'status_filter': status_filter,
        'teams': teams,
    }
    
    return render(request, 'admin/players.html', context)


# --- NUEVAS VISTAS ---
@login_required
@user_passes_test(is_admin)
def admin_add_player(request):
    """Vista para agregar un nuevo jugador."""
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jugador agregado exitosamente.')
            return redirect('admin_panel:players')
    else:
        form = PlayerForm()
    
    context = {
        'form': form,
        'title': 'Agregar Jugador'
    }
    return render(request, 'admin/player_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_player(request, player_id):
    """Vista para editar un jugador existente."""
    player = get_object_or_404(Player, id=player_id)
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jugador actualizado exitosamente.')
            return redirect('admin_panel:players')
    else:
        form = PlayerForm(instance=player)
        
    context = {
        'form': form,
        'title': 'Editar Jugador'
    }
    return render(request, 'admin/player_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_delete_player(request, player_id):
    """Vista para eliminar un jugador."""
    player = get_object_or_404(Player, id=player_id)
    if request.method == 'POST':
        player.delete()
        messages.success(request, 'Jugador eliminado exitosamente.')
        return redirect('admin_panel:players')
    
    return render(request, 'admin/player_confirm_delete.html', {'player': player})

# --- FIN DE NUEVAS VISTAS ---


@login_required
@user_passes_test(is_admin)
def admin_registrations(request):
# ... (resto del código sin cambios) ...
    """Manage player registrations"""
    status_filter = request.GET.get('status', 'pending')
    
    registrations = Registration.objects.all()
    
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    registrations = registrations.order_by('-created_at')
    
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
    """Aprueba una solicitud de registro de jugador."""
    if request.method == 'POST':
        registration = get_object_or_404(Registration, id=registration_id, status='pending')
        
        # 1. Crear la categoría si no existe
        category, _ = Category.objects.get_or_create(name=registration.team)
        
        # 2. Crear el nuevo jugador
        player = Player.objects.create(
            first_name=registration.player_first_name,
            last_name=registration.player_last_name,
            rut=registration.player_rut,
            birthdate=registration.player_birth_date,
            category=category,
            status='active' # Se establece como activo por defecto
        )
        
        # 3. Crear la relación entre el apoderado y el jugador
        GuardianPlayer.objects.create(
            guardian=registration.guardian,
            player=player,
            relation='tutor' # Relación por defecto, se puede mejorar después
        )
        
        # 4. Actualizar el estado de la solicitud
        registration.status = 'approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        messages.success(request, f'El jugador {player.get_full_name()} ha sido aprobado y creado exitosamente.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@user_passes_test(is_admin)
def admin_reject_registration(request, registration_id):
    """Rechaza una solicitud de registro de jugador."""
    if request.method == 'POST':
        registration = get_object_or_404(Registration, id=registration_id, status='pending')
        
        # Actualizar el estado de la solicitud
        registration.status = 'rejected'
        registration.rejection_reason = request.POST.get('reason', 'Sin motivo especificado.')
        registration.save()
        
        messages.warning(request, f'La solicitud para {registration.player_first_name} {registration.player_last_name} ha sido rechazada.')
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@user_passes_test(is_admin)
def admin_finances(request):
    """Manage finances"""
    total_income = Payment.objects.filter(status='completado').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    pending_payments = Invoice.objects.filter(status='pendiente').count()
    overdue_payments = Invoice.objects.filter(status='atrasada').count()
    
    recent_payments = Payment.objects.order_by('-created_at')[:10]
    
    monthly_income = []
    for i in range(6):
        month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        income = Payment.objects.filter(
            status='completado',
            created_at__gte=month_start,
            created_at__lt=month_end
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
    recent_messages = BulkEmail.objects.order_by('-created_at')[:10]
    
    context = {
        'messages': recent_messages,
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
        
        recipients = User.objects.none()
        
        if recipient_type == 'all':
            recipients = User.objects.all()
        elif recipient_type == 'guardians':
            recipients = User.objects.filter(guardian_profile__isnull=False)
        elif recipient_type == 'admins':
            recipients = User.objects.filter(admin_profile__isnull=False)
        
        if recipients.exists():
            bulk_email = BulkEmail.objects.create(
                title=title,
                body_html=message,
                created_by=request.user,
                is_sent=True,
                sent_at=timezone.now()
            )
            
            email_recipients = [
                EmailRecipient(bulk_email=bulk_email, user=user, status='enviado', sent_at=timezone.now())
                for user in recipients
            ]
            EmailRecipient.objects.bulk_create(email_recipients)
            
            messages.success(request, f'Comunicación enviada a {len(email_recipients)} usuarios.')
        else:
            messages.warning(request, 'No se encontraron destinatarios para esta comunicación.')

        return redirect('admin_panel:communications')
    
    return render(request, 'admin/send_notification.html')


@login_required
@user_passes_test(is_admin)
def admin_sponsors(request):
    """Manage sponsors"""
    sponsors = Sponsor.objects.all().order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        sponsors = sponsors.filter(active=True)
    elif status_filter == 'inactive':
        sponsors = sponsors.filter(active=False)
    
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
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    players = Player.objects.select_related('category').all()
    
    if category_filter:
        players = players.filter(category_id=category_filter)
    
    if search_query:
        players = players.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    players = players.order_by('category__name', 'last_name')
    
    paginator = Paginator(players, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin/player_cards.html', context)