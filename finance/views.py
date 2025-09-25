from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Payment, Invoice
from users.admin_views import is_admin # Reutilizamos la función de validación

@login_required
def financial_report_view(request):
    """
    Vista para que un administrador vea un resumen de las finanzas.
    """
    if not is_admin(request.user):
        return redirect('pages:landing')

    total_income = Payment.objects.filter(status='completado').aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = Invoice.objects.filter(status__in=['pendiente', 'atrasada']).aggregate(total=Sum('amount'))['total'] or 0
    
    recent_payments = Payment.objects.filter(status='completado').order_by('-paid_at')[:20]

    context = {
        'total_income': total_income,
        'pending_amount': pending_amount,
        'recent_payments': recent_payments,
    }
    return render(request, 'finance/financial_report.html', context)