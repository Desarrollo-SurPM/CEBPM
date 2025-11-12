from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ticket, TicketReply
from .forms import TicketForm, ReplyForm
from users.guardian_views import is_guardian # Reutilizamos tu helper

@login_required
def list_tickets(request):
    # ... (esta vista está bien, no hay cambios) ...
    if not is_guardian(request.user):
        messages.error(request, "Acceso no autorizado.")
        return redirect('pages:landing')

    tickets = Ticket.objects.filter(guardian=request.user)
    context = {
        'tickets': tickets,
        'page_title': 'Mis Solicitudes'
    }
    return render(request, 'tickets/list_tickets.html', context)

@login_required
def create_ticket(request):
    # ... (esta vista está bien, no hay cambios) ...
    if not is_guardian(request.user):
        messages.error(request, "Acceso no autorizado.")
        return redirect('pages:landing')

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            # Creamos el Ticket
            ticket = form.save(commit=False)
            ticket.guardian = request.user
            ticket.status = 'abierto'
            ticket.save()
            
            # Creamos la primera Respuesta
            TicketReply.objects.create(
                ticket=ticket,
                user=request.user,
                message=form.cleaned_data['message']
            )
            
            messages.success(request, 'Tu solicitud ha sido enviada. Un administrador te responderá pronto.')
            return redirect('tickets:list')
    else:
        form = TicketForm()

    context = {
        'form': form,
        'page_title': 'Crear Nueva Solicitud'
    }
    return render(request, 'tickets/create_ticket.html', context)

@login_required
def view_ticket(request, pk):
    """
    Muestra un ticket específico y sus respuestas.
    Permite al apoderado añadir una nueva respuesta.
    """
    if not is_guardian(request.user):
        messages.error(request, "Acceso no autorizado.")
        return redirect('pages:landing')

    ticket = get_object_or_404(Ticket, pk=pk, guardian=request.user)
    replies = ticket.replies.all().select_related('user')

    if request.method == 'POST':
        reply_form = ReplyForm(request.POST)
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.ticket = ticket
            reply.user = request.user
            reply.save()
            
            # Si el apoderado responde, lo marcamos como 'abierto' de nuevo
            ticket.status = 'abierto'
            ticket.save()
            
            messages.success(request, 'Tu respuesta ha sido añadida.')
            return redirect('tickets:view', pk=ticket.pk)
    else:
        reply_form = ReplyForm()
        
    # --- INICIO DE LA CORRECCIÓN ---
    # HEMOS ELIMINADO EL BLOQUE 'if ticket.status == respondido'
    # El ticket ya no se cierra automáticamente al leerlo.
    # --- FIN DE LA CORRECCIÓN ---

    context = {
        'ticket': ticket,
        'replies': replies,
        'reply_form': reply_form,
        'page_title': f'Viendo Ticket #{ticket.id}'
    }
    return render(request, 'tickets/view_ticket.html', context)