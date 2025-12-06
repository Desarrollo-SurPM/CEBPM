from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
import json

# Importaciones de Modelos
from pages.models import LandingNews, LandingEvent
from pages.forms import LandingNewsForm, LandingEventForm
from .models import User, GuardianProfile, AdminProfile, Registration
from players.models import Player, GuardianPlayer, Category, PlayerDocument
from finance.models import Payment, FeeDefinition, Invoice, Transaction
from sponsors.models import Sponsor
from schedules.models import Match, Activity
from communications.models import BulkEmail, EmailRecipient
from tickets.models import Ticket, TicketReply

# Importaciones de Formularios
from .forms import UserRegistrationForm, GuardianProfileForm, AdminProfileForm, UserUpdateForm, CategoryForm
from players.forms import PlayerForm, PlayerDocumentForm
from finance.forms import FeeDefinitionForm, TransactionForm, AssignFeeForm
from tickets.forms import ReplyForm
# IMPORTANTE: Importamos el formulario desde su ubicación correcta
from sponsors.forms import SponsorForm

def is_admin(user):
    if not user.is_authenticated: return False
    return hasattr(user, 'admin_profile')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Estadísticas
    total_players = Player.objects.count()
    total_guardians = GuardianProfile.objects.count()
    total_paid_quotas = Invoice.objects.filter(status='pagada').aggregate(Sum('amount'))['amount__sum'] or 0
    total_pending_quotas = Invoice.objects.filter(status__in=['pendiente', 'en revisión']).aggregate(Sum('amount'))['amount__sum'] or 0
    total_overdue_quotas = Invoice.objects.filter(status='atrasada').aggregate(Sum('amount'))['amount__sum'] or 0
    total_funds = Payment.objects.filter(status='completado').aggregate(Sum('amount'))['amount__sum'] or 0
    
    active_sponsors = Sponsor.objects.filter(is_visible=True).count()
    pending_registrations = Registration.objects.filter(status='pending').count()
    
    # Mensuales
    current_month = timezone.now().replace(day=1)
    monthly_registrations = Registration.objects.filter(created_at__gte=current_month).count()
    monthly_payments = Payment.objects.filter(created_at__gte=current_month, status='completado').count()

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
        'monthly_registrations': monthly_registrations,
        'monthly_payments': monthly_payments,
        'recent_registrations': Registration.objects.order_by('-created_at')[:5],
        'recent_payments': Payment.objects.filter(status='completado').order_by('-created_at')[:5],
        'upcoming_matches': Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:5],
    }
    return render(request, 'admin/dashboard.html', context)

# --- REGISTROS ---
@login_required
@user_passes_test(is_admin)
def admin_registrations(request):
    # Lógica del filtro: Si es None (entrada directa), forzar 'pending'.
    # Si es '' (clic en "Todas"), mostrar todo.
    status_filter = request.GET.get('status')
    if status_filter is None:
        status_filter = 'pending'
    
    registrations = Registration.objects.all().order_by('-created_at')
    
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    paginator = Paginator(registrations, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'page_obj': page_obj, 
        'status_filter': status_filter
    }
    return render(request, 'admin/registrations.html', context)

@login_required
@user_passes_test(is_admin)
def admin_approve_registration(request, registration_id):
    if request.method == 'POST':
        reg = get_object_or_404(Registration, id=registration_id)
        try:
            category = Category.objects.get(name=reg.team)
        except Category.DoesNotExist:
            category = Category.objects.first()

        player = Player.objects.create(
            first_name=reg.player_first_name, last_name=reg.player_last_name,
            rut=reg.player_rut, birthdate=reg.player_birth_date,
            category=category, status='active'
        )
        GuardianPlayer.objects.create(guardian=reg.guardian, player=player, relation='tutor')
        reg.guardian.is_active = True
        reg.guardian.save()
        
        reg.status = 'approved'; reg.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
@user_passes_test(is_admin)
def admin_reject_registration(request, registration_id):
    if request.method == 'POST':
        reg = get_object_or_404(Registration, id=registration_id)
        reg.status = 'rejected'
        reg.rejection_reason = request.POST.get('reason', '')
        reg.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# --- SPONSORS (CORREGIDO) ---
@login_required
@user_passes_test(is_admin)
def admin_sponsors(request):
    """Maneja la lista y creación de auspiciadores"""
    
    # 1. Manejo del Formulario
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Auspiciador creado correctamente.')
            # CORRECCIÓN AQUÍ: Cambiamos 'sponsors' por 'admin_sponsors' 
            # para que coincida con name='admin_sponsors' en admin_urls.py
            return redirect('admin_panel:admin_sponsors') 
        else:
            messages.error(request, 'Error al crear. Revisa los datos.')
    else:
        form = SponsorForm()

    # 2. Listado y Filtros
    sponsors_query = Sponsor.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    
    if status_filter == 'active':
        sponsors_query = sponsors_query.filter(is_visible=True)
    elif status_filter == 'inactive':
        sponsors_query = sponsors_query.filter(is_visible=False)
    
    paginator = Paginator(sponsors_query, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'sponsors': page_obj, 
        'page_obj': page_obj,
        'form': form,
        'status_filter': status_filter
    }
    return render(request, 'admin/sponsors.html', context)

# ... al final del archivo ...

@login_required
@user_passes_test(is_admin)
def edit_sponsor(request, pk):
    """Editar un auspiciador existente"""
    sponsor = get_object_or_404(Sponsor, pk=pk)
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES, instance=sponsor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Auspiciador actualizado.')
            return redirect('admin_panel:admin_sponsors')
    else:
        form = SponsorForm(instance=sponsor)
    
    return render(request, 'admin/sponsor_edit.html', {'form': form, 'sponsor': sponsor})

@login_required
@user_passes_test(is_admin)
def delete_sponsor(request, pk):
    """Eliminar un auspiciador"""
    if request.method == 'POST':
        sponsor = get_object_or_404(Sponsor, pk=pk)
        sponsor.delete()
        messages.success(request, 'Auspiciador eliminado.')
    return redirect('admin_panel:admin_sponsors')
# --- FINANZAS ---
@login_required
@user_passes_test(is_admin)
def admin_finances(request):
    total_income = Transaction.objects.filter(type='ingreso').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(type='gasto').aggregate(Sum('amount'))['amount__sum'] or 0
    
    transactions_list = Transaction.objects.all().order_by('-date')
    paginator = Paginator(transactions_list, 25)
    transactions_page = paginator.get_page(request.GET.get('page'))
    
    today = timezone.now().date()
    current_month_start = date(today.year, today.month, 1)
    months_dt = []
    cm = current_month_start
    for _ in range(12):
        months_dt.insert(0, cm)
        if cm.month == 1:
            cm = date(cm.year - 1, 12, 1)
        else:
            cm = date(cm.year, cm.month - 1, 1)
    monthly_labels = [m.strftime('%b %Y') for m in months_dt]
    monthly_income = []
    monthly_expenses = []
    for m in months_dt:
        income_total = Transaction.objects.filter(type='ingreso', date__year=m.year, date__month=m.month).aggregate(Sum('amount'))['amount__sum'] or 0
        expense_total = Transaction.objects.filter(type='gasto', date__year=m.year, date__month=m.month).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_income.append(float(income_total))
        monthly_expenses.append(float(expense_total))

    category_display = dict(Transaction.CATEGORY_CHOICES)
    income_agg = Transaction.objects.filter(type='ingreso').values('category').annotate(total=Sum('amount')).order_by('-total')
    expense_agg = Transaction.objects.filter(type='gasto').values('category').annotate(total=Sum('amount')).order_by('-total')
    income_categories = [category_display.get(row['category'], row['category']) for row in income_agg]
    income_amounts = [float(row['total'] or 0) for row in income_agg]
    expense_categories = [category_display.get(row['category'], row['category']) for row in expense_agg]
    expense_amounts = [float(row['total'] or 0) for row in expense_agg]

    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'transactions': transactions_page,
        'players': Player.objects.all().order_by('first_name'),
        'pending_payments': Payment.objects.filter(status='pendiente').aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_payments_count': Payment.objects.filter(status='pendiente').count(),
        'page_title': 'Gestión Financiera',
        'monthly_labels': monthly_labels,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'income_categories': income_categories,
        'income_amounts': income_amounts,
        'expense_categories': expense_categories,
        'expense_amounts': expense_amounts,
    }
    return render(request, 'admin/finances.html', context)

@login_required
@user_passes_test(is_admin)
def add_transaction(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            player = None
            if data.get('player'):
                player = Player.objects.get(id=data.get('player'))
            
            Transaction.objects.create(
                type=data['type'], category=data['category'], 
                description=data['description'], amount=data['amount'], date=data['date'],
                player=player
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

# --- CUOTAS ---
@login_required
@user_passes_test(is_admin)
def manage_fee_definitions(request):
    """Gestión de Tipos de Cuotas (Agrupadas por Categoría)"""
    if request.method == 'POST':
        form = FeeDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nueva tarifa creada correctamente.')
            return redirect('admin_panel:manage_fees')
        else:
            messages.error(request, 'Error al crear la tarifa. Revisa los datos.')
    else:
        form = FeeDefinitionForm()

    # --- Lógica de Agrupación ---
    grouped_fees = []
    
    # 1. Cuotas Generales (Sin categoría, aplican a todos)
    general_fees = FeeDefinition.objects.filter(category__isnull=True).order_by('name')
    grouped_fees.append({
        'id': 'general',
        'name': 'General / Transversal',
        'icon': 'bi-globe',
        'fees': general_fees,
        'count': general_fees.count(),
        'style': 'primary' # Color distintivo
    })
    
    # 2. Cuotas por Categoría
    categories = Category.objects.all().order_by('name')
    for cat in categories:
        fees = FeeDefinition.objects.filter(category=cat).order_by('name')
        grouped_fees.append({
            'id': f'cat_{cat.id}',
            'name': cat.name,
            'icon': 'bi-people-fill',
            'fees': fees,
            'count': fees.count(),
            'style': 'dark'
        })

    context = {
        'form': form,
        'grouped_fees': grouped_fees,
        'page_title': 'Definición de Cuotas'
    }
    return render(request, 'admin/manage_fees.html', context)

@login_required
@user_passes_test(is_admin)
def edit_fee_definition(request, pk):
    fee = get_object_or_404(FeeDefinition, pk=pk)
    if request.method == 'POST':
        form = FeeDefinitionForm(request.POST, instance=fee)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_fees')
    else: form = FeeDefinitionForm(instance=fee)
    return render(request, 'admin/manage_fees_edit.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_fee_definition(request, pk):
    if request.method == 'POST': get_object_or_404(FeeDefinition, pk=pk).delete()
    return redirect('admin_panel:manage_fees')

@login_required
@user_passes_test(is_admin)
def manage_pending_payments(request):
    return render(request, 'admin/manage_payments.html', {
        'payments': Payment.objects.filter(status='pendiente').order_by('paid_at')
    })

@login_required
@user_passes_test(is_admin)
def review_payment(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'admin/review_payment.html', {'payment': payment, 'invoice': payment.invoice})

@login_required
@user_passes_test(is_admin)
def approve_payment(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Payment, pk=pk)
        p.status = 'completado'; p.save()
        p.invoice.status = 'pagada'; p.invoice.save()
    return redirect('admin_panel:manage_pending_payments')

@login_required
@user_passes_test(is_admin)
def reject_payment(request, pk):
    if request.method == 'POST':
        p = get_object_or_404(Payment, pk=pk)
        p.status = 'fallido'; p.save()
        p.invoice.status = 'pendiente'; p.invoice.save()
    return redirect('admin_panel:manage_pending_payments')

# --- JUGADORES ---
@login_required
@user_passes_test(is_admin)
def admin_players(request):
    search = request.GET.get('search', '')
    players = Player.objects.all().order_by('last_name')
    if search: players = players.filter(Q(first_name__icontains=search)|Q(last_name__icontains=search))
    
    paginator = Paginator(players, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'admin/players.html', {'page_obj': page_obj, 'search_query': search, 'teams': Category.objects.values_list('name', flat=True).distinct()})

@login_required
@user_passes_test(is_admin)
def admin_player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    inv = Invoice.objects.filter(player=player)
    context = {
        'player': player,
        'guardian_links': GuardianPlayer.objects.filter(player=player),
        'paid_invoices': inv.filter(status='pagada'),
        'pending_invoices': inv.exclude(status='pagada'),
        'total_debt': inv.exclude(status='pagada').aggregate(Sum('amount'))['amount__sum'] or 0,
        'documents': PlayerDocument.objects.filter(player=player),
        'upload_form': PlayerDocumentForm()
    }
    return render(request, 'admin/player_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_edit_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES, instance=player)
        if form.is_valid(): form.save(); return redirect('admin_panel:admin_player_detail', pk=pk)
    else: form = PlayerForm(instance=player)
    return render(request, 'admin/player_edit.html', {'form': form, 'player': player})

@login_required
@user_passes_test(is_admin)
def admin_add_player_document(request, player_pk):
    if request.method == 'POST':
        form = PlayerDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            d = form.save(commit=False); d.player_id = player_pk; d.uploaded_by = request.user; d.save()
    return redirect('admin_panel:admin_player_detail', pk=player_pk)

@login_required
@user_passes_test(is_admin)
def admin_player_cards(request):
    return render(request, 'admin/player_cards.html', {'categories': Category.objects.all()})

# --- COMUNICACIONES Y OTROS ---
@login_required
@user_passes_test(is_admin)
def admin_communications(request):
    return render(request, 'admin/communications.html', {
        'messages_list': BulkEmail.objects.all().order_by('-created_at')[:10],
        'categories': Category.objects.all()
    })

@login_required
@user_passes_test(is_admin)
def admin_send_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        body = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')
        attachment = request.FILES.get('attachment')
        
        recipients = User.objects.none()
        if recipient_type == 'all_guardians':
            recipients = User.objects.filter(guardian_profile__isnull=False, is_active=True)
        
        if recipients.exists():
            bulk = BulkEmail.objects.create(title=title, body_html=body, created_by=request.user, is_sent=True, sent_at=timezone.now(), attachment=attachment)
            EmailRecipient.objects.bulk_create([EmailRecipient(bulk_email=bulk, user=u, status='enviado', sent_at=timezone.now()) for u in recipients])
            messages.success(request, 'Mensaje enviado.')
    return redirect('admin_panel:communications')

@login_required
@user_passes_test(is_admin)
def communication_status(request, pk):
    msg = get_object_or_404(BulkEmail, pk=pk)
    return render(request, 'admin/communication_status.html', {'message': msg, 'recipients_list': msg.recipients.all()})

@login_required
@user_passes_test(is_admin)
def manage_landing_news(request):
    if request.method == 'POST':
        form = LandingNewsForm(request.POST, request.FILES)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_news')
    return render(request, 'admin/manage_news.html', {'news_list': LandingNews.objects.all(), 'form': LandingNewsForm()})

@login_required
@user_passes_test(is_admin)
def edit_landing_news(request, pk):
    item = get_object_or_404(LandingNews, pk=pk)
    if request.method == 'POST':
        form = LandingNewsForm(request.POST, request.FILES, instance=item)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_news')
    return render(request, 'admin/manage_news_edit.html', {'form': LandingNewsForm(instance=item)})

@login_required
@user_passes_test(is_admin)
def delete_landing_news(request, pk):
    if request.method == 'POST': get_object_or_404(LandingNews, pk=pk).delete()
    return redirect('admin_panel:manage_news')

@login_required
@user_passes_test(is_admin)
def manage_landing_calendar(request):
    """
    Vista principal del calendario.
    AHORA SEPARA: Partidos, Entrenamientos y Actividades.
    """
    today = timezone.now()
    context = {
        'matches': Match.objects.filter(starts_at__gte=today).order_by('starts_at'),
        
        # Filtramos explícitamente por tipo
        'trainings': Activity.objects.filter(starts_at__gte=today, type='entrenamiento').order_by('starts_at'),
        'activities': Activity.objects.filter(starts_at__gte=today, type='otro').order_by('starts_at'),
        
        'categories': Category.objects.all(),
        'page_title': 'Gestión de Calendario'
    }
    return render(request, 'admin/manage_calendar.html', context)

@login_required
@user_passes_test(is_admin)
def edit_landing_event(request, pk):
    item = get_object_or_404(LandingEvent, pk=pk)
    if request.method == 'POST':
        form = LandingEventForm(request.POST, instance=item)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_calendar')
    return render(request, 'admin/manage_calendar_edit.html', {'form': LandingEventForm(instance=item)})

@login_required
@user_passes_test(is_admin)
def add_activity(request):
    """Crea actividades especiales (Reuniones, Eventos)"""
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        starts_at = request.POST.get('starts_at')
        ends_at = request.POST.get('ends_at')
        location = request.POST.get('location')
        description = request.POST.get('description') # Campo extra para detalles
        
        category = None
        if category_id:
            category = Category.objects.get(id=category_id)
            
        Activity.objects.create(
            title=title,
            type='otro', # Importante: Tipo 'otro'
            category=category,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            description=description
        )
        messages.success(request, 'Actividad creada correctamente.')
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def delete_landing_event(request, pk):
    if request.method == 'POST': get_object_or_404(LandingEvent, pk=pk).delete()
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def manage_featured_players(request):
    if request.method == 'POST':
        ids = request.POST.getlist('featured_players')
        if len(ids) > 4: messages.error(request, 'Máximo 4 jugadoras'); return redirect('admin_panel:manage_featured_players')
        Player.objects.all().update(is_featured=False)
        Player.objects.filter(id__in=ids).update(is_featured=True)
        return redirect('admin_panel:manage_featured_players')
    return render(request, 'admin/manage_featured_players.html', {'all_players': Player.objects.all(), 'featured_count': Player.objects.filter(is_featured=True).count()})

@login_required
@user_passes_test(is_admin)
def manage_categories(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_categories')
    return render(request, 'admin/manage_categories.html', {'categories': Category.objects.all(), 'form': CategoryForm()})

@login_required
@user_passes_test(is_admin)
def toggle_category_registration(request, pk):
    if request.method == 'POST':
        c = get_object_or_404(Category, pk=pk)
        c.is_registration_open = not c.is_registration_open; c.save()
    return redirect('admin_panel:manage_categories')

@login_required
@user_passes_test(is_admin)
def assign_fees_to_category(request):
    """
    Vista para asignar cuotas masivas (por categoría) o individuales.
    """
    if request.method == 'POST':
        # Obtenemos datos directos del request para mayor control
        fee_id = request.POST.get('fee_definition')
        due_date = request.POST.get('due_date')
        target_type = request.POST.get('target_type')
        
        try:
            fee_def = FeeDefinition.objects.get(id=fee_id)
            invoices_created = 0
            
            # --- CASO 1: Por Categoría ---
            if target_type == 'category':
                cat_id = request.POST.get('category')
                if not cat_id:
                    messages.error(request, 'Debes seleccionar una categoría.')
                    return redirect('admin_panel:assign_fees')
                
                # Buscar jugadores activos de esa categoría que tengan apoderado
                # Usamos guardianplayer__isnull=False para asegurar que tengan quien pague
                target_players = Player.objects.filter(
                    category_id=cat_id, 
                    status='active',
                    guardianplayer__isnull=False 
                ).distinct()
                
            # --- CASO 2: Jugador Individual ---
            else:
                player_id = request.POST.get('player')
                if not player_id:
                    messages.error(request, 'Debes buscar y seleccionar un jugador.')
                    return redirect('admin_panel:assign_fees')
                
                target_players = Player.objects.filter(id=player_id)

            # --- Generación de Cobros ---
            for player in target_players:
                # Obtener al apoderado (asumimos el primero si hay varios, o el tutor principal)
                guardian_link = GuardianPlayer.objects.filter(player=player).first()
                if guardian_link:
                    # Crear la factura (Invoice)
                    Invoice.objects.create(
                        guardian=guardian_link.guardian,
                        player=player,
                        fee_definition=fee_def,
                        amount=fee_def.amount, # Monto congelado al momento de asignar
                        due_date=due_date,
                        status='pendiente'
                    )
                    invoices_created += 1
            
            if invoices_created > 0:
                messages.success(request, f'Se generaron {invoices_created} cobros exitosamente.')
                return redirect('admin_panel:manage_pending_payments') # Éxito: Ir a revisión
            else:
                messages.warning(request, 'No se generaron cobros. Revisa que los jugadores tengan apoderado asignado.')
                
        except Exception as e:
            messages.error(request, f'Ocurrió un error: {str(e)}')
            
    # --- CONTEXTO PARA EL TEMPLATE ---
    # Esto es lo que faltaba para llenar los selectores:
    context = {
        'fees': FeeDefinition.objects.all(),
        'categories': Category.objects.all(),
        # Enviamos 'all_players' para el buscador TomSelect
        'all_players': Player.objects.filter(status='active').select_related('category').order_by('first_name'),
        'page_title': 'Asignar Cobros'
    }
    return render(request, 'admin/assign_fees.html', context)

# --- TICKETS ---
@login_required
@user_passes_test(is_admin)
def list_admin_tickets(request):
    status_filter = request.GET.get('status', 'abierto')
    qs = Ticket.objects.all() if status_filter == 'todos' else Ticket.objects.filter(status=status_filter)
    paginator = Paginator(qs, 20)
    return render(request, 'admin/admin_tickets_list.html', {'page_obj': paginator.get_page(request.GET.get('page')), 'status_filter': status_filter})

@login_required
@user_passes_test(is_admin)
def view_admin_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False); r.ticket = ticket; r.user = request.user; r.save()
            ticket.status = 'respondido'; ticket.save()
            return redirect('admin_panel:admin_ticket_view', pk=pk)
    return render(request, 'admin/admin_ticket_view.html', {'ticket': ticket, 'replies': ticket.replies.all(), 'reply_form': ReplyForm()})

@login_required
@user_passes_test(is_admin)
def close_admin_ticket(request, pk):
    if request.method == 'POST':
        t = get_object_or_404(Ticket, pk=pk); t.status = 'cerrado'; t.save()
        return redirect('admin_panel:list_admin_tickets')
    return redirect('admin_panel:admin_ticket_view', pk=pk)

# VISTAS INDIVIDUALES QUE FALTABAN
@login_required
@user_passes_test(is_admin)
def add_match(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        opponent = request.POST.get('opponent')
        starts_at = request.POST.get('starts_at')
        location = request.POST.get('location')
        
        category = Category.objects.get(id=category_id)
        Match.objects.create(category=category, opponent=opponent, starts_at=starts_at, location=location)
        messages.success(request, 'Partido creado.')
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def delete_match(request, pk):
    if request.method == 'POST':
        get_object_or_404(Match, pk=pk).delete()
        messages.success(request, 'Partido eliminado.')
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def add_training(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        starts_at = request.POST.get('starts_at')
        ends_at = request.POST.get('ends_at')
        location = request.POST.get('location')
        
        category = None
        if category_id: category = Category.objects.get(id=category_id)
            
        Activity.objects.create(title=title, type='entrenamiento', category=category, starts_at=starts_at, ends_at=ends_at, location=location)
        messages.success(request, 'Entrenamiento creado.')
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def delete_activity(request, pk):
    if request.method == 'POST':
        get_object_or_404(Activity, pk=pk).delete()
        messages.success(request, 'Actividad eliminada.')
    return redirect('admin_panel:manage_calendar')

@login_required
@user_passes_test(is_admin)
def bulk_schedule_trainings(request):
    """
    Vista innovadora para crear entrenamientos recurrentes o masivos.
    Permite seleccionar múltiples categorías y días.
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        location = request.POST.get('location')
        start_time = request.POST.get('start_time') # Hora inicio (HH:MM)
        end_time = request.POST.get('end_time')     # Hora fin (HH:MM)
        start_date = request.POST.get('start_date') # Fecha inicio ciclo
        end_date = request.POST.get('end_date')     # Fecha fin ciclo
        
        # Listas de selección múltiple
        selected_categories = request.POST.getlist('categories') # IDs de categorías
        selected_weekdays = request.POST.getlist('weekdays')     # ['0', '2', '4'] (Lunes, Miér, Vier)
        
        # Conversión de datos
        from datetime import datetime, time
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Validar horas
        h_start = datetime.strptime(start_time, "%H:%M").time()
        h_end = datetime.strptime(end_time, "%H:%M").time()

        created_count = 0
        
        # Iterar por cada día en el rango de fechas
        current_date = s_date
        while current_date <= e_date:
            # Si el día de la semana coincide con los seleccionados
            # weekday(): 0=Lunes, 6=Domingo
            if str(current_date.weekday()) in selected_weekdays:
                
                # Para cada categoría seleccionada, creamos el evento
                for cat_id in selected_categories:
                    cat = Category.objects.get(id=cat_id)
                    
                    # Combinar fecha y hora
                    dt_start = datetime.combine(current_date, h_start)
                    dt_end = datetime.combine(current_date, h_end)
                    
                    # Hacerlo timezone aware si usas USE_TZ=True
                    dt_start = timezone.make_aware(dt_start)
                    dt_end = timezone.make_aware(dt_end)

                    Activity.objects.create(
                        title=title,
                        type='entrenamiento',
                        category=cat,
                        starts_at=dt_start,
                        ends_at=dt_end,
                        location=location
                    )
                    created_count += 1
            
            current_date += timedelta(days=1)

        messages.success(request, f'¡Éxito! Se generaron {created_count} sesiones de entrenamiento.')
        return redirect('admin_panel:manage_calendar')

    context = {
        'categories': Category.objects.all().order_by('name'),
        'page_title': 'Programación Masiva'
    }
    return render(request, 'admin/bulk_schedule.html', context)