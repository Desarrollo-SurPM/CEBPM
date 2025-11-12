from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from finance.forms import FeeDefinitionForm, TransactionForm, AssignFeeForm
from django.db.models import Count, Q, Sum, F, ExpressionWrapper, fields
from django.db import models
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models.functions import TruncMonth
from players.forms import PlayerForm
import json
from datetime import datetime, timedelta
from tickets.models import Ticket, TicketReply # <-- NUEVA IMPORTACIÓN
from tickets.forms import ReplyForm # <-- NUEVA IMPORTACIÓN

# Importaciones de modelos y formularios
from pages.models import LandingNews, LandingEvent
from pages.forms import LandingNewsForm, LandingEventForm
from .models import User, GuardianProfile, AdminProfile, Registration
from players.models import Player, GuardianPlayer, Category # <-- Importar Category
from finance.models import Payment, FeeDefinition, Invoice, Transaction
from sponsors.models import Sponsor
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient
from players.models import Player, GuardianPlayer, Category, PlayerDocument # <-- Añadir PlayerDocument
from players.forms import PlayerForm, PlayerDocumentForm # <-- Añadir PlayerDocumentForm

# --- CORRECCIÓN DE IMPORTACIÓN ---
# CategoryForm está en '.forms' (users/forms.py), no en 'finance.forms'
from .forms import UserRegistrationForm, GuardianProfileForm, AdminProfileForm, UserUpdateForm, CategoryForm
from finance.forms import FeeDefinitionForm, TransactionForm
# --- FIN DE CORRECCIÓN ---


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
    total_players = Player.objects.count()
    total_guardians = GuardianProfile.objects.count()
    
    total_paid_quotas = Invoice.objects.filter(status='pagada').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_pending_quotas = Invoice.objects.filter(status__in=['pendiente', 'en revisión']).aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_overdue_quotas = Invoice.objects.filter(status='atrasada').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_funds = Payment.objects.filter(status='completado').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    active_sponsors = Sponsor.objects.filter(active=True).count()
    pending_registrations = Registration.objects.filter(status='pending').count()
    
    current_month = timezone.now().replace(day=1)
    monthly_registrations = Registration.objects.filter(
        created_at__gte=current_month
    ).count()
    monthly_payments = Payment.objects.filter(
        created_at__gte=current_month,
        status='completado'
    ).count()

    recent_registrations = Registration.objects.order_by('-created_at')[:5]
    recent_payments = Payment.objects.filter(status='completado').order_by('-created_at')[:5]
    upcoming_matches = Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:5]
    
    context = {
        'total_players': total_players,
        'total_guardians': total_guardians,
        'total_payments': monthly_payments,
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


# ==============================================
# VISTA DE FINANZAS (COMPLETA)
# ==============================================
@login_required
@user_passes_test(is_admin)
def admin_finances(request):
    """
    Dashboard financiero unificado:
    Combina Cuotas (Payments) e Ingresos/Gastos (Transactions)
    para alimentar la plantilla 'finances.html'
    """
    
    # 1. TARJETAS DE RESUMEN
    total_income = Transaction.objects.filter(type='ingreso').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    total_expenses = Transaction.objects.filter(type='gasto').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    balance = total_income - total_expenses
    
    pending_payments_sum = Payment.objects.filter(status='pendiente').aggregate(
        total=Sum('amount')
    )['total'] or 0
        
    pending_payments_count = Payment.objects.filter(status='pendiente').count()

    # 2. GRÁFICO DE LÍNEAS (12 MESES)
    monthly_labels = []
    monthly_income_data = []
    monthly_expense_data = []
    
    today = timezone.now().date()
    current_date = today.replace(day=1)

    for _ in range(12):
        monthly_labels.insert(0, current_date.strftime("%b %Y"))
        
        next_month = (current_date + timedelta(days=32)).replace(day=1)
        
        income = Transaction.objects.filter(
            type='ingreso', 
            date__gte=current_date, 
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense = Transaction.objects.filter(
            type='gasto', 
            date__gte=current_date, 
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_income_data.insert(0, float(income))
        monthly_expense_data.insert(0, float(expense))
        
        last_day_of_prev_month = current_date - timedelta(days=1)
        current_date = last_day_of_prev_month.replace(day=1)

    # 3. GRÁFICO DE DONA (DISTRIBUCIÓN DE INGRESOS)
    income_by_category = Transaction.objects.filter(
        type='ingreso'
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    category_map = dict(Transaction.CATEGORY_CHOICES)
    income_categories = [category_map.get(item['category'], item['category']) for item in income_by_category]
    income_amounts = [float(item['total']) for item in income_by_category]

    # 4. TABLA DE TRANSACCIONES (CON FILTROS)
    transactions_list = Transaction.objects.all().order_by('-date')
    
    type_filter = request.GET.get('type')
    category_filter = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if type_filter:
        transactions_list = transactions_list.filter(type=type_filter)
    if category_filter:
        transactions_list = transactions_list.filter(category=category_filter)
    if date_from:
        transactions_list = transactions_list.filter(date__gte=date_from)
    if date_to:
        transactions_list = transactions_list.filter(date__lte=date_to)
    if search:
        transactions_list = transactions_list.filter(description__icontains=search)
        
    # 5. PAGINACIÓN (para la tabla)
    paginator = Paginator(transactions_list, 25)
    page_number = request.GET.get('page')
    transactions_page = paginator.get_page(page_number)
    
    # 6. DATOS PARA EL MODAL
    players = Player.objects.all().order_by('first_name')
    
    # 7. CONTEXTO
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'pending_payments': pending_payments_sum,
        'balance': balance,
        
        'pending_payments_count': pending_payments_count,

        'monthly_labels': json.dumps(monthly_labels),
        'monthly_income': json.dumps(monthly_income_data),
        'monthly_expenses': json.dumps(monthly_expense_data),
        'income_categories': json.dumps(income_categories),
        'income_amounts': json.dumps(income_amounts),
        
        'transactions': transactions_page,
        'players': players,
        
        'page_title': 'Gestión Financiera'
    }
    
    return render(request, 'admin/finances.html', context)


@login_required
@user_passes_test(is_admin)
def add_transaction(request):
    """
    Vista para manejar el POST del modal 'Registrar Nueva Transacción'
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            player_instance = None
            player_id = data.get('player')
            if player_id:
                player_instance = Player.objects.get(id=player_id)
            
            Transaction.objects.create(
                type=data['type'],
                category=data['category'],
                description=data['description'],
                amount=data['amount'],
                date=data['date'],
                player=player_instance
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


# --- Vistas de Gestión de Cuotas (del paso anterior) ---

@login_required
@user_passes_test(is_admin)
def manage_fee_definitions(request):
    """
    (Parte A) CRUD para Definiciones de Cuotas (Matrícula, Mensualidad)
    """
    if request.method == 'POST':
        form = FeeDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Definición de cuota creada exitosamente.')
            return redirect('admin_panel:manage_fees')
        else:
            messages.error(request, 'Error al crear la definición de cuota.')
    else:
        form = FeeDefinitionForm()

    fee_definitions = FeeDefinition.objects.all().order_by('name')
    context = {
        'form': form,
        'fees': fee_definitions,
        'page_title': 'Definiciones de Cuotas'
    }
    return render(request, 'admin/manage_fees.html', context)

@login_required
@user_passes_test(is_admin)
def edit_fee_definition(request, pk):
    """Editar una Definición de Cuota"""
    fee = get_object_or_404(FeeDefinition, pk=pk)
    if request.method == 'POST':
        form = FeeDefinitionForm(request.POST, instance=fee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Definición actualizada.')
            return redirect('admin_panel:manage_fees')
    else:
        form = FeeDefinitionForm(instance=fee)
    
    context = {
        'form': form,
        'page_title': f'Editando: {fee.name}'
    }
    return render(request, 'admin/manage_fees_edit.html', context)


@login_required
@user_passes_test(is_admin)
def delete_fee_definition(request, pk):
    """Eliminar una Definición de Cuota"""
    fee = get_object_or_404(FeeDefinition, pk=pk)
    if request.method == 'POST':
        fee.delete()
        messages.success(request, 'Definición de cuota eliminada.')
    return redirect('admin_panel:manage_fees')


@login_required
@user_passes_test(is_admin)
def manage_pending_payments(request):
    """
    (Parte B) Ver Pagos Pendientes de Aprobación
    """
    pending_payments_list = Payment.objects.filter(status='pendiente').order_by('paid_at')
    
    context = {
        'payments': pending_payments_list,
        'page_title': 'Pagos Pendientes de Aprobación'
    }
    return render(request, 'admin/manage_payments.html', context)


@login_required
@user_passes_test(is_admin)
def review_payment(request, pk):
    """Revisar un pago individual (ver comprobante, aprobar/rechazar)"""
    payment = get_object_or_404(Payment, pk=pk, status='pendiente')
    invoice = payment.invoice
    
    context = {
        'payment': payment,
        'invoice': invoice,
        'guardian': invoice.guardian,
        'player': invoice.player,
        'page_title': f'Revisar Pago #{payment.id}'
    }
    return render(request, 'admin/review_payment.html', context)


@login_required
@user_passes_test(is_admin)
def approve_payment(request, pk):
    """Aprueba un pago pendiente"""
    if request.method != 'POST':
        return redirect('admin_panel:manage_pending_payments')
        
    payment = get_object_or_404(Payment, pk=pk, status='pendiente')
    invoice = payment.invoice
    
    payment.status = 'completado'
    payment.save()
    
    invoice.status = 'pagada'
    invoice.save()
    
    messages.success(request, f'Pago #{payment.id} aprobado. La factura #{invoice.id} está ahora pagada.')
    return redirect('admin_panel:manage_pending_payments')


@login_required
@user_passes_test(is_admin)
def reject_payment(request, pk):
    """Rechaza un pago pendiente"""
    if request.method != 'POST':
        return redirect('admin_panel:manage_pending_payments')
        
    payment = get_object_or_404(Payment, pk=pk, status='pendiente')
    invoice = payment.invoice
    
    payment.status = 'fallido' 
    payment.save()
    
    if invoice.due_date < timezone.now().date():
        invoice.status = 'atrasada'
    else:
        invoice.status = 'pendiente'
    invoice.save()
    
    rejection_reason = request.POST.get('rejection_reason', 'Sin motivo especificado.')
    
    messages.warning(request, f'Pago #{payment.id} rechazado (Motivo: {rejection_reason}). La factura #{invoice.id} ha sido revertida a {invoice.status}.')
    return redirect('admin_panel:manage_pending_payments')


# --- Resto de Vistas del Admin (Jugadores, Registros, Landing, etc.) ---

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
        players = players.filter(status=status_filter)
    
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

@login_required
@user_passes_test(is_admin)
def admin_player_detail(request, pk):
    """
    Muestra el perfil detallado de una jugadora, incluyendo sus datos,
    apoderados e historial financiero.
    """
    try:
        player = Player.objects.select_related('category').get(pk=pk)
    except Player.DoesNotExist:
        messages.error(request, 'La jugadora solicitada no existe.')
        return redirect('admin_panel:players')

    # 1. Obtener apoderados
    guardian_links = GuardianPlayer.objects.filter(player=player).select_related('guardian', 'guardian__guardian_profile')
    
    # 2. Obtener historial financiero
    invoices = Invoice.objects.filter(player=player).order_by('-due_date')
    
    paid_invoices = invoices.filter(status='pagada')
    pending_invoices = invoices.filter(status__in=['pendiente', 'atrasada', 'en revisión'])
    
    total_debt = pending_invoices.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = paid_invoices.aggregate(total=Sum('amount'))['total'] or 0

# --- NUEVA LÓGICA AÑADIDA ---
    documents = PlayerDocument.objects.filter(player=player)
    upload_form = PlayerDocumentForm()
    # --- FIN NUEVA LÓGICA ---

    context = {
        'player': player,
        'guardian_links': guardian_links,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'total_debt': total_debt,
        'total_paid': total_paid,
        'documents': documents,       # <-- AÑADIDO
        'upload_form': upload_form,
        'page_title': f'Perfil de: {player.get_full_name()}'
    }
    return render(request, 'admin/player_detail.html', context)

# --- AÑADIR ESTA NUEVA VISTA ---
@login_required
@user_passes_test(is_admin)
def admin_edit_player(request, pk):
    """
    Permite al Admin editar la ficha completa de una jugadora.
    """
    player = get_object_or_404(Player, pk=pk)
    
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ficha de {player.get_full_name()} actualizada correctamente.')
            return redirect('admin_panel:admin_player_detail', pk=player.pk)
        else:
            messages.error(request, 'Error al actualizar la ficha. Revisa los campos.')
    else:
        form = PlayerForm(instance=player)

    context = {
        'form': form,
        'player': player,
        'page_title': f'Editando Ficha: {player.get_full_name()}'
    }
    return render(request, 'admin/player_edit.html', context)
# --- FIN DE VISTA AÑADIDA ---

# --- AÑADIR ESTA NUEVA VISTA ---
@login_required
@user_passes_test(is_admin)
def admin_add_player_document(request, player_pk):
    """
    Maneja la subida de un nuevo documento para la jugadora desde el panel de admin.
    """
    player = get_object_or_404(Player, pk=player_pk)
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
    
    # Siempre redirigir de vuelta al detalle del jugador
    return redirect('admin_panel:admin_player_detail', pk=player_pk)

@login_required
@user_passes_test(is_admin)
def admin_registrations(request):
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
        
        category = get_object_or_404(Category, name=registration.team)
        
        player = Player.objects.create(
            first_name=registration.player_first_name,
            last_name=registration.player_last_name,
            rut=registration.player_rut,
            birthdate=registration.player_birth_date,
            category=category,
            status='active'
        )
        
        GuardianPlayer.objects.create(
            guardian=registration.guardian,
            player=player,
            relation='tutor'
        )
        
        # --- ACTIVAR LA CUENTA DEL APODERADO ---
        guardian_user = registration.guardian
        guardian_user.is_active = True
        guardian_user.save()
        # --- FIN DE LA ACTIVACIÓN ---

        registration.status = 'approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        
        messages.success(request, f'El jugador {player.get_full_name()} ha sido aprobado. La cuenta del apoderado {guardian_user.get_full_name()} ha sido activada.')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
@user_passes_test(is_admin)
def admin_reject_registration(request, registration_id):
    """Rechaza una solicitud de registro de jugador."""
    if request.method == 'POST':
        registration = get_object_or_404(Registration, id=registration_id, status='pending')
        
        # Opcional: Eliminar el User y GuardianProfile inactivos
        try:
            guardian_user = registration.guardian
            if not guardian_user.is_active:
                guardian_user.delete() # Esto borra el User y el GuardianProfile en cascada
        except User.DoesNotExist:
            pass # El usuario ya fue borrado

        registration.status = 'rejected'
        registration.rejection_reason = request.POST.get('reason', 'Sin motivo especificado.')
        registration.save()
        
        messages.warning(request, f'La solicitud para {registration.player_first_name} {registration.player_last_name} ha sido rechazada.')
        return JsonResponse({'success': True})
        
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@user_passes_test(is_admin)
def admin_communications(request):
    """Muestra el formulario de envío e historial de comunicaciones."""
    recent_messages = BulkEmail.objects.order_by('-created_at')[:10]
    categories = Category.objects.all() # <-- AÑADIDO
    
    context = {
        'messages_list': recent_messages, # <-- CAMBIADO el nombre de la variable
        'categories': categories, # <-- AÑADIDO
    }
    
    return render(request, 'admin/communications.html', context)


@login_required
@user_passes_test(is_admin)
def admin_send_notification(request):
    """Envía notificaciones al panel (con adjuntos, sin correo)."""
    if request.method == 'POST':
        title = request.POST.get('title')
        message_body = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')
        
        # --- NUEVO: Manejo de Archivo Adjunto ---
        attachment_file = request.FILES.get('attachment') 

        recipients = User.objects.none()
        
        if recipient_type == 'all_guardians':
            recipients = User.objects.filter(guardian_profile__isnull=False, is_active=True)
        
        elif recipient_type == 'all_admins':
            recipients = User.objects.filter(admin_profile__isnull=False, is_active=True)
        
        elif recipient_type == 'multiple_categories':
            category_ids = request.POST.getlist('category')
            if category_ids:
                players = Player.objects.filter(category_id__in=category_ids, status='active')
                guardian_ids = GuardianPlayer.objects.filter(player__in=players).values_list('guardian_id', flat=True).distinct()
                recipients = User.objects.filter(id__in=guardian_ids, is_active=True)
            
        elif recipient_type == 'specific_email':
            email = request.POST.get('specific_email')
            if email:
                recipients = User.objects.filter(email__iexact=email, is_active=True)

        # --- Lógica de Envío (Modificada) ---
        if recipients.exists():
            # 1. Crear el mensaje masivo (con el adjunto)
            bulk_email = BulkEmail.objects.create(
                title=title,
                body_html=message_body,
                created_by=request.user,
                is_sent=True,
                sent_at=timezone.now(),
                attachment=attachment_file # <-- Guardar el archivo
            )
            
            email_recipients_list = []
            for user in recipients:
                email_recipients_list.append(
                    EmailRecipient(bulk_email=bulk_email, user=user, status='enviado', sent_at=timezone.now())
                )
            
            # 2. Guardar en la Base de Datos (para el panel del apoderado)
            EmailRecipient.objects.bulk_create(email_recipients_list)
            
            # 3. (ELIMINADO) La lógica de 'send_mail' se ha quitado.
            
            messages.success(request, f'Mensaje enviado al panel de {len(email_recipients_list)} usuarios.')

        else:
            messages.warning(request, 'No se encontraron destinatarios para esta comunicación.')

        return redirect('admin_panel:communications')
    
    return redirect('admin_panel:communications')


@login_required
@user_passes_test(is_admin)
def communication_status(request, pk):
    """
    Vista de Admin para ver quién ha leído un mensaje específico.
    """
    try:
        bulk_message = BulkEmail.objects.get(pk=pk)
    except BulkEmail.DoesNotExist:
        messages.error(request, "El mensaje que intentas ver no existe.")
        return redirect('admin_panel:communications')

    # Obtenemos todos los destinatarios de este mensaje
    recipients = EmailRecipient.objects.filter(
        bulk_email=bulk_message
    ).select_related('user').order_by('user__last_name')

    context = {
        'message': bulk_message,
        'recipients_list': recipients,
        'page_title': f"Estado de Lectura: {bulk_message.title}"
    }
    return render(request, 'admin/communication_status.html', context)

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

# --- Vistas de Gestión de Landing ---

@login_required
@user_passes_test(is_admin)
def manage_landing_news(request):
    """Listar y Agregar Noticias de Landing"""
    if request.method == 'POST':
        form = LandingNewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia creada exitosamente.')
            return redirect('admin_panel:manage_news')
        else:
            messages.error(request, 'Hubo un error en el formulario.')
    else:
        form = LandingNewsForm()

    news_list = LandingNews.objects.all().order_by('-created_at')
    context = {
        'form': form,
        'news_list': news_list,
        'page_title': 'Gestionar Noticias de Landing'
    }
    return render(request, 'admin/manage_news.html', context)


@login_required
@user_passes_test(is_admin)
def edit_landing_news(request, pk):
    """Editar Noticia de Landing"""
    news_item = get_object_or_404(LandingNews, pk=pk)
    if request.method == 'POST':
        form = LandingNewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('admin_panel:manage_news')
        else:
            messages.error(request, 'Hubo un error al actualizar.')
    else:
        form = LandingNewsForm(instance=news_item)

    context = {
        'form': form,
        'page_title': f'Editando: {news_item.title}'
    }
    return render(request, 'admin/manage_news_edit.html', context)

@login_required
@user_passes_test(is_admin)
def delete_landing_news(request, pk):
    """Eliminar Noticia de Landing"""
    news_item = get_object_or_404(LandingNews, pk=pk)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'Noticia eliminada exitosamente.')
        return redirect('admin_panel:manage_news')
    
    return redirect('admin_panel:manage_news')


@login_required
@user_passes_test(is_admin)
def manage_landing_calendar(request):
    """Listar y Agregar Eventos de Calendario de Landing"""
    if request.method == 'POST':
        form = LandingEventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento creado exitosamente.')
            return redirect('admin_panel:manage_calendar')
        else:
            messages.error(request, 'Hubo un error en el formulario.')
    else:
        form = LandingEventForm()

    event_list = LandingEvent.objects.all().order_by('date')
    context = {
        'form': form,
        'event_list': event_list,
        'page_title': 'Gestionar Calendario de Landing'
    }
    return render(request, 'admin/manage_calendar.html', context)

@login_required
@user_passes_test(is_admin)
def edit_landing_event(request, pk):
    """Editar Evento de Calendario"""
    event_item = get_object_or_404(LandingEvent, pk=pk)
    if request.method == 'POST':
        form = LandingEventForm(request.POST, instance=event_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento actualizado exitosamente.')
            return redirect('admin_panel:manage_calendar')
    else:
        form = LandingEventForm(instance=event_item)

    context = {
        'form': form,
        'page_title': f'Editando: {event_item.title}'
    }
    return render(request, 'admin/manage_calendar_edit.html', context)

@login_required
@user_passes_test(is_admin)
def delete_landing_event(request, pk):
    """Eliminar Evento de Calendario"""
    event_item = get_object_or_404(LandingEvent, pk=pk)
    if request.method == 'POST':
        event_item.delete()
        messages.success(request, 'Evento eliminado exitosamente.')
        return redirect('admin_panel:manage_calendar')
    
    return redirect('admin_panel:manage_calendar')


@login_required
@user_passes_test(is_admin)
def manage_featured_players(request):
    """Gestionar las 4 Jugadoras Destacadas de la Landing"""
    if request.method == 'POST':
        selected_player_ids = request.POST.getlist('featured_players')
        
        if len(selected_player_ids) > 4:
            messages.error(request, 'Error: Solo puedes seleccionar un máximo de 4 jugadoras.')
        else:
            Player.objects.all().update(is_featured=False)
            Player.objects.filter(id__in=selected_player_ids).update(is_featured=True)
            messages.success(request, 'Jugadoras destacadas actualizadas correctamente.')
        
        return redirect('admin_panel:manage_featured_players')

    all_players = Player.objects.all().order_by('category', 'last_name')
    featured_players = Player.objects.filter(is_featured=True)
    
    context = {
        'all_players': all_players,
        'featured_count': featured_players.count(),
        'page_title': 'Gestionar Jugadoras Destacadas'
    }
    return render(request, 'admin/manage_featured_players.html', context)


# --- VISTA DE GESTIÓN DE CATEGORÍAS (NUEVA) ---
@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    """
    Vista de Admin para CRUD de Categorías y
    para ABRIR/CERRAR inscripciones.
    """
    if request.method == 'POST':
        # Lógica para crear una nueva categoría
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categoría '{form.cleaned_data['name']}' creada.")
            return redirect('admin_panel:manage_categories')
    else:
        form = CategoryForm()

    categories = Category.objects.all().order_by('name')
    context = {
        'form': form,
        'categories': categories,
        'page_title': 'Gestionar Categorías e Inscripciones'
    }
    return render(request, 'admin/manage_categories.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_category_registration(request, pk):
    """Activa o desactiva las inscripciones para una categoría"""
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category.is_registration_open = not category.is_registration_open
        category.save()
        status = "abiertas" if category.is_registration_open else "cerradas"
        messages.success(request, f"Inscripciones para {category.name} ahora están {status}.")
    return redirect('admin_panel:manage_categories')

@login_required
@user_passes_test(is_admin)
def assign_fees_to_category(request):
    """
    Vista de Admin para asignar masivamente una cuota (FeeDefinition) 
    a todas las jugadoras de una Categoría.
    """
    if request.method == 'POST':
        form = AssignFeeForm(request.POST)
        if form.is_valid():
            fee_definition = form.cleaned_data['fee_definition']
            category = form.cleaned_data['category']
            due_date = form.cleaned_data['due_date']
            
            # 1. Encontrar a todas las jugadoras activas en esa categoría
            players_in_category = Player.objects.filter(
                category=category, 
                status='active'
            )
            
            # 2. Encontrar a sus apoderados (GuardianPlayer)
            # Usamos select_related para optimizar la consulta
            guardian_players = GuardianPlayer.objects.filter(
                player__in=players_in_category
            ).select_related('guardian', 'player')
            
            invoices_created = 0
            invoices_skipped = 0
            
            # 3. Iterar y crear las facturas (Invoices)
            for gp in guardian_players:
                # 4. (Clave) Revisar si esta jugadora YA tiene esta factura
                exists = Invoice.objects.filter(
                    player=gp.player,
                    fee_definition=fee_definition
                ).exists()
                
                if not exists:
                    try:
                        Invoice.objects.create(
                            guardian=gp.guardian,
                            player=gp.player,
                            fee_definition=fee_definition,
                            amount=fee_definition.amount, # Tomamos el monto de la definición
                            due_date=due_date,
                            status='pendiente' # ¡Lista para ser pagada!
                        )
                        invoices_created += 1
                    except IntegrityError:
                        # Por si acaso (carrera de condiciones)
                        invoices_skipped += 1
                else:
                    invoices_skipped += 1
                    
            messages.success(request, f"Proceso completado: {invoices_created} nuevas facturas creadas. {invoices_skipped} jugadoras ya tenían esta cuota y fueron omitidas.")
            return redirect('admin_panel:manage_fees') # Redirige de vuelta a la gestión de cuotas

    else:
        form = AssignFeeForm()

    context = {
        'form': form,
        'page_title': 'Asignar Cuotas Masivamente'
    }
    return render(request, 'admin/assign_fees.html', context)

# --- INICIO VISTAS DE TICKETS (ADMIN) ---

@login_required
@user_passes_test(is_admin)
def list_admin_tickets(request):
    """
    Muestra al admin la lista de todos los tickets.
    """
    status_filter = request.GET.get('status', 'abierto') # Ver 'abiertos' por defecto
    
    if status_filter == 'todos':
        ticket_list = Ticket.objects.all()
    else:
        ticket_list = Ticket.objects.filter(status=status_filter)
        
    paginator = Paginator(ticket_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'page_title': 'Gestión de Solicitudes'
    }
    return render(request, 'admin/admin_tickets_list.html', context)

@login_required
@user_passes_test(is_admin)
def view_admin_ticket(request, pk):
    """
    Permite al admin ver un ticket y responder.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    replies = ticket.replies.all().select_related('user')

    if request.method == 'POST':
        reply_form = ReplyForm(request.POST)
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.ticket = ticket
            reply.user = request.user # La respuesta es del Admin
            reply.save()
            
            # Si el admin responde, lo marca como 'respondido'
            ticket.status = 'respondido'
            ticket.save()
            
            messages.success(request, 'Tu respuesta ha sido enviada al apoderado.')
            return redirect('admin_panel:admin_ticket_view', pk=ticket.pk)
    else:
        reply_form = ReplyForm()

    context = {
        'ticket': ticket,
        'replies': replies,
        'reply_form': reply_form,
        'page_title': f'Respondiendo Ticket #{ticket.id}'
    }
    return render(request, 'admin/admin_ticket_view.html', context)

# --- AÑADIR ESTA NUEVA FUNCIÓN ---

@login_required
@user_passes_test(is_admin)
def close_admin_ticket(request, pk):
    """
    Permite al admin cerrar un ticket manualmente.
    """
    ticket = get_object_or_404(Ticket, pk=pk)
    
    if request.method == 'POST':
        ticket.status = 'cerrado'
        ticket.save()
        messages.success(request, f"El Ticket #{ticket.id} ('{ticket.subject}') ha sido marcado como 'Cerrado'.")
        # Redirigir de vuelta a la lista de tickets
        return redirect('admin_panel:admin_tickets_list')
    
    # Si se accede por GET, simplemente redirigir a la vista de detalle
    return redirect('admin_panel:admin_ticket_view', pk=pk)
# --- FIN VISTAS DE TICKETS (ADMIN) ---