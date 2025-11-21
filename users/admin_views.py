from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
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
    
    # 1. Manejo del Formulario (POST = Guardar, GET = Vacío)
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Auspiciador creado correctamente.')
            return redirect('admin_panel:sponsors')
        else:
            messages.error(request, 'Error al crear. Revisa los datos.')
    else:
        form = SponsorForm()

    # 2. Listado
    sponsors_query = Sponsor.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status')
    
    if status_filter == 'active':
        sponsors_query = sponsors_query.filter(is_visible=True)
    elif status_filter == 'inactive':
        sponsors_query = sponsors_query.filter(is_visible=False)
    
    paginator = Paginator(sponsors_query, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'sponsors': page_obj, # Tu HTML usa 'sponsors'
        'page_obj': page_obj,
        'form': form,         # IMPORTANTE: Enviamos el form para que se vea
        'status_filter': status_filter
    }
    return render(request, 'admin/sponsors.html', context)

# --- FINANZAS ---
@login_required
@user_passes_test(is_admin)
def admin_finances(request):
    total_income = Transaction.objects.filter(type='ingreso').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = Transaction.objects.filter(type='gasto').aggregate(Sum('amount'))['amount__sum'] or 0
    
    transactions_list = Transaction.objects.all().order_by('-date')
    paginator = Paginator(transactions_list, 25)
    transactions_page = paginator.get_page(request.GET.get('page'))
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'transactions': transactions_page,
        'players': Player.objects.all().order_by('first_name'),
        'pending_payments': Payment.objects.filter(status='pendiente').aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_payments_count': Payment.objects.filter(status='pendiente').count(),
        'page_title': 'Gestión Financiera'
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
    if request.method == 'POST':
        form = FeeDefinitionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuota creada.')
            return redirect('admin_panel:manage_fees')
    else:
        form = FeeDefinitionForm()
    return render(request, 'admin/manage_fees.html', {'form': form, 'fees': FeeDefinition.objects.all()})

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
    if request.method == 'POST':
        form = LandingEventForm(request.POST)
        if form.is_valid(): form.save(); return redirect('admin_panel:manage_calendar')
    return render(request, 'admin/manage_calendar.html', {'event_list': LandingEvent.objects.all(), 'form': LandingEventForm()})

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
    if request.method == 'POST':
        form = AssignFeeForm(request.POST)
        if form.is_valid():
            fd, cat, date = form.cleaned_data['fee_definition'], form.cleaned_data['category'], form.cleaned_data['due_date']
            for gp in GuardianPlayer.objects.filter(player__category=cat, player__status='active'):
                if not Invoice.objects.filter(player=gp.player, fee_definition=fd).exists():
                    Invoice.objects.create(guardian=gp.guardian, player=gp.player, fee_definition=fd, amount=fd.amount, due_date=date, status='pendiente')
            return redirect('admin_panel:manage_fees')
    return render(request, 'admin/assign_fees.html', {'form': AssignFeeForm()})

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