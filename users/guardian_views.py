from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.contrib.auth.models import User

# --- INICIO DE IMPORTACIONES CORREGIDAS ---
from players.forms import PlayerGuardianEditForm, PlayerDocumentForm
from players.models import Player, GuardianPlayer, Category, PlayerDocument 
# Formularios
from .forms import GuardianProfileForm, UserUpdateForm, PlayerRegistrationForm
from players.forms import PlayerGuardianEditForm
# Usamos el 'PlayerForm' completo (del admin) para registrar jugadoras nuevas
from players.forms import PlayerForm as PlayerFullForm 

# Modelos (importados desde sus apps correctas)
from .models import GuardianProfile, Registration # Modelos de Users
from players.models import Player, GuardianPlayer, Category # Modelos de Players
from finance.models import Invoice, Payment
from schedules.models import Match, Activity
from communications.models import EmailRecipient, BulkEmail

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
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    players = Player.objects.filter(id__in=guardian_players.values_list('player_id', flat=True))
    
    # Estadísticas
    total_players = players.count()
    active_players = players.filter(status='active').count()
    
    pending_payments = Invoice.objects.filter(
        player__in=players,
        status__in=['pendiente', 'atrasada']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    unread_messages = EmailRecipient.objects.filter(
        user=request.user,
        read_at__isnull=True
    ).count()
    
    # Eventos próximos
    today = timezone.now().date()
    player_categories = players.values_list('category', flat=True)
    upcoming_matches = Match.objects.filter(
        category__id__in=player_categories,
        starts_at__gte=today
    ).order_by('starts_at')[:5]
    
    recent_payments = Payment.objects.filter(
        invoice__player__in=players
    ).order_by('-paid_at')[:5]
    
    context = {
        'players': players,
        'total_players': total_players,
        'active_players': active_players,
        'pending_payments': pending_payments,
        'unread_messages': unread_messages,
        'upcoming_matches': upcoming_matches,
        'recent_payments': recent_payments,
    }
    return render(request, 'guardian/dashboard.html', context)

@login_required
def guardian_profile(request):
    """Muestra y actualiza el perfil del apoderado (Maneja JSON para el template actual)."""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    profile, created = GuardianProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Detectar si es una petición AJAX (fetch)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'multipart/form-data' or True # Forzamos compatibilidad con tu JS
        
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = GuardianProfileForm(request.POST, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            if is_ajax:
                return JsonResponse({'success': True, 'message': 'Perfil actualizado'})
            messages.success(request, 'Perfil actualizado.')
            return redirect('guardian:profile')
        else:
            errors = {**u_form.errors, **p_form.errors}
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(errors)})
            messages.error(request, 'Error al actualizar.')
    
    password_form = PasswordChangeForm(request.user)
    context = {
        'user': request.user,
        'profile': profile,
        'password_form': password_form,
    }
    return render(request, 'guardian/profile.html', context)

@login_required
def add_new_player(request):
    """Registrar nueva jugadora desde el panel del apoderado"""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            # Crear la solicitud (Registration) vinculada al apoderado actual
            registration = form.save(commit=False)
            registration.guardian = request.user
            registration.status = 'pending'
            
            # Asignar categoría automáticamente si es posible o dejar que el admin decida
            # Aquí asumimos que el formulario ya trae el 'team' (Categoría) seleccionado
            
            registration.save()
            messages.success(request, 'Solicitud de inscripción enviada. Esperando aprobación.')
            return redirect('guardian:guardian_players')
        else:
            messages.error(request, 'Error en el formulario. Revisa los datos.')
    else:
        form = PlayerRegistrationForm()

    return render(request, 'guardian/player_add.html', {'form': form})

@login_required
def guardian_edit_player(request, pk):
    """Edición de ficha de jugadora"""
    if not is_guardian(request.user):
        return redirect('pages:landing')

    # Verificar propiedad
    guardian_player = get_object_or_404(GuardianPlayer, guardian=request.user, player_id=pk)
    player = guardian_player.player

    if request.method == 'POST':
        form = PlayerGuardianEditForm(request.POST, request.FILES, instance=player)
        
        # Capturamos la fecha manualmente si el formulario no la incluye pero el template sí
        birthdate = request.POST.get('birthdate')
        if birthdate:
            player.birthdate = birthdate

        if form.is_valid():
            player.save() # Esto guarda el form y la fecha asignada manualmente
            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('guardian:player_detail', player_id=player.pk)
    else:
        form = PlayerGuardianEditForm(instance=player)

    context = {'form': form, 'player': player, 'page_title': f'Editar: {player.get_full_name()}'}
    return render(request, 'guardian/player_edit.html', context)

# ... (Mantener el resto de las vistas como guardian_players, guardian_payments, etc. que ya funcionaban bien)
# Asegúrate de incluir change_password, update_notifications, etc.
@login_required
@require_http_methods(["POST"])
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': form.errors.as_text()})

@login_required
@require_http_methods(["POST"])
def update_notifications(request):
    profile = get_object_or_404(GuardianProfile, user=request.user)
    profile.email_notifications = 'email_notifications' in request.POST
    profile.save()
    return JsonResponse({'success': True})

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
    """Muestra los mensajes y notificaciones enviadas por el admin al apoderado."""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')

    # 1. Obtener los *recibos* de email para este usuario
    user_messages = EmailRecipient.objects.filter(
        user=request.user
    ).select_related('bulk_email').order_by('-sent_at')

    # --- CORRECCIÓN ---
    # 2. YA NO marcamos como leídos automáticamente.
    # user_messages.filter(read_at__isnull=True).update(read_at=timezone.now())
    # --- FIN CORRECCIÓN ---

    context = {
        'messages_list': user_messages,
        'page_title': 'Mis Mensajes y Notificaciones'
    }
    return render(request, 'guardian/messages.html', context)

@login_required
def guardian_view_message(request, pk):
    """
    Muestra un mensaje específico y lo marca como leído.
    """
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    # 1. Obtener el "recibo" del mensaje
    recipient_message = get_object_or_404(
        EmailRecipient, 
        pk=pk, 
        user=request.user
    )
    
    # 2. Marcar como leído (¡Esta es la lógica clave!)
    if recipient_message.read_at is None:
        recipient_message.read_at = timezone.now()
        recipient_message.save()

    context = {
        'recipient': recipient_message,
        'message': recipient_message.bulk_email, # El contenido del mensaje
        'page_title': 'Leyendo Mensaje'
    }
    return render(request, 'guardian/message_detail.html', context)

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
    documents = PlayerDocument.objects.filter(player=player)
    upload_form = PlayerDocumentForm()

    context = {
        'player': player,
        'invoices': invoices[:10],  # Últimas 10 facturas
        'paid_invoices_count': paid_invoices.count(),
        'pending_invoices_count': pending_invoices.count(),
        'overdue_invoices_count': overdue_invoices.count(),
        'total_paid': total_paid,
        'documents': documents,       # <-- AÑADIDO
        'upload_form': upload_form,
        'total_pending': total_pending,
        'total_overdue': total_overdue,
        'upcoming_matches': upcoming_matches,
        'upcoming_trainings': upcoming_trainings,
    }
    
    return render(request, 'guardian/player_detail.html', context)

@login_required
def guardian_add_player_document(request, player_pk):
    """
    Maneja la subida de un nuevo documento para la jugadora desde el panel del apoderado.
    """
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos.')
        return redirect('pages:landing')
    
    # Seguridad: Asegurarse de que esta jugadora pertenece a este apoderado
    try:
        player = Player.objects.get(pk=player_pk)
        GuardianPlayer.objects.get(player=player, guardian=request.user)
    except (Player.DoesNotExist, GuardianPlayer.DoesNotExist):
        messages.error(request, 'No tienes permiso para esta acción.')
        return redirect('guardian:guardian_players')

    if request.method == 'POST':
        form = PlayerDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.player = player
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, f"Documento '{doc.title}' subido exitosamente.")
        else:
            messages.error(request, "Error al subir el documento.")
    
    return redirect('guardian:player_detail', pk=player_pk)

@login_required
def guardian_edit_player(request, pk):
    """
    Permite al apoderado editar la información de su jugadora.
    """
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')

    # Seguridad: Asegurarse de que esta jugadora pertenece a este apoderado
    try:
        player = Player.objects.get(pk=pk)
        GuardianPlayer.objects.get(player=player, guardian=request.user)
    except (Player.DoesNotExist, GuardianPlayer.DoesNotExist):
        messages.error(request, 'No tienes permiso para editar esta jugadora.')
        return redirect('guardian:guardian_players')

    if request.method == 'POST':
        form = PlayerGuardianEditForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'Datos de {player.get_full_name()} actualizados.')
            return redirect('guardian:player_detail', pk=player.pk)
    else:
        form = PlayerGuardianEditForm(instance=player)

    context = {
        'form': form,
        'player': player,
        'page_title': f'Editando Ficha: {player.get_full_name()}'
    }
    return render(request, 'guardian/player_edit.html', context)

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
    """Vista para pagar una cuota específica (subir comprobante)"""
    if not is_guardian(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('pages:landing')
    
    guardian_players = GuardianPlayer.objects.filter(guardian=request.user)
    player_ids = guardian_players.values_list('player_id', flat=True)
    invoice = get_object_or_404(Invoice, id=invoice_id, player_id__in=player_ids)
    
    # Verificar que la cuota no esté ya pagada o en revisión
    if invoice.status == 'pagada':
        messages.warning(request, 'Esta cuota ya ha sido pagada.')
        return redirect('guardian:guardian_quotas_paid')
    if invoice.status == 'en revisión':
        messages.warning(request, 'Esta cuota ya está en revisión.')
        return redirect('guardian:guardian_quotas_upcoming')

    if request.method == 'POST':
        # --- Lógica para procesar el formulario ---
        payment_method = request.POST.get('payment_method')
        reference_number = request.POST.get('reference_number', '')
        payment_proof_file = request.FILES.get('payment_proof') # <-- OBTENER EL ARCHIVO

        # Validaciones
        if not payment_method:
            messages.error(request, 'Debes seleccionar un método de pago.')
            return redirect('guardian:guardian_pay_quota', invoice_id=invoice.id)
        
        if not payment_proof_file:
            messages.error(request, 'Debes subir un comprobante de pago.')
            return redirect('guardian:guardian_pay_quota', invoice_id=invoice.id)

        # Crear el objeto Payment
        Payment.objects.create(
            invoice=invoice,
            amount=invoice.amount,
            paid_at=timezone.now(), # Se marca la fecha de subida
            method=payment_method,
            status='pendiente', # Pendiente de aprobación
            payment_proof=payment_proof_file, # Guardar el archivo
            notes=reference_number
        )
        
        # Actualizar el estado de la factura a "En Revisión"
        invoice.status = 'en revisión'
        invoice.save()
        
        messages.success(request, f'Pago de ${invoice.amount:,.0f} enviado para revisión. Será aprobado por un administrador.')
        return redirect('guardian:guardian_quotas_upcoming')
    
    # --- Lógica GET (mostrar la página) ---
    context = {
        'invoice': invoice,
        'player': invoice.player,
        'today': timezone.now().date() # Añadido para la lógica del template
    }
    
    return render(request, 'guardian/pay_quota.html', context)

@login_required
def profile_view(request):
    # CORRECCIÓN: Usar get_or_create para evitar error si el perfil no existe
    profile, created = GuardianProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = GuardianProfileForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, '¡Tu cuenta ha sido actualizada!')
            return redirect('guardian_profile') # Asegúrate que este name exista en urls.py
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = GuardianProfileForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'guardian/profile.html', context)

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