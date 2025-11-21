from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import FeeDefinition, Invoice, Payment


@admin.register(FeeDefinition)
class FeeDefinitionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'amount', 'period', 'created_at']
    list_filter = ['period', 'category', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'category', 'amount', 'period')
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # Modificado: 'is_overdue_display' ya no es necesario si 'save' maneja el estado
    list_display = ['get_guardian_name', 'get_player_name', 'amount', 'due_date', 'status']
    list_filter = ['status', 'due_date', 'created_at']
    search_fields = ['guardian__first_name', 'guardian__last_name', 'player__first_name', 'player__last_name']
    date_hierarchy = 'due_date'
    ordering = ['-due_date']
    
    fieldsets = (
        ('Información de la Factura', {
            'fields': ('guardian', 'player', 'fee_definition', 'amount', 'due_date')
        }),
        ('Estado', {
            'fields': ('status',)
        })
    )
    
    actions = ['mark_as_paid', 'mark_as_pending']
    
    def get_guardian_name(self, obj):
        return f"{obj.guardian.first_name} {obj.guardian.last_name}"
    get_guardian_name.short_description = 'Apoderado'
    get_guardian_name.admin_order_field = 'guardian__first_name'
    
    def get_player_name(self, obj):
        if obj.player:
            return f"{obj.player.first_name} {obj.player.last_name}"
        return 'N/A'
    get_player_name.short_description = 'Jugador'
    get_player_name.admin_order_field = 'player__first_name'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='pagada')
        self.message_user(request, f'{updated} facturas marcadas como pagadas.')
    mark_as_paid.short_description = 'Marcar como pagada'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pendiente')
        self.message_user(request, f'{updated} facturas marcadas como pendientes.')
    mark_as_pending.short_description = 'Marcar como pendiente'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # --- MODIFICADO ---
    # 1. Cambiado 'transaction_id' por 'notes'
    # 2. Añadido 'get_payment_proof' para ver el comprobante
    list_display = ['get_invoice_info', 'amount', 'paid_at', 'method', 'status', 'notes', 'get_payment_proof']
    list_filter = ['status', 'method', 'paid_at', 'created_at']
    # 3. Cambiado 'transaction_id' por 'notes' en la búsqueda
    search_fields = ['invoice__guardian__first_name', 'invoice__guardian__last_name', 'notes']
    date_hierarchy = 'paid_at'
    ordering = ['-paid_at']
    
    # 4. Cambiado 'transaction_id' por 'notes' y 'payment_proof'
    fieldsets = (
        ('Información del Pago', {
            'fields': ('invoice', 'amount', 'paid_at', 'method')
        }),
        ('Estado y Comprobante', {
            'fields': ('status', 'notes', 'payment_proof')
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def get_invoice_info(self, obj):
        return f"Factura #{obj.invoice.id} - {obj.invoice.guardian.first_name} {obj.invoice.guardian.last_name}"
    get_invoice_info.short_description = 'Factura'
    get_invoice_info.admin_order_field = 'invoice__id'

    # --- NUEVO MÉTODO ---
    # 5. Para mostrar un enlace al comprobante en la lista
    def get_payment_proof(self, obj):
        if obj.payment_proof:
            return format_html('<a href="{}" target="_blank">Ver Comprobante</a>', obj.payment_proof.url)
        return "N/A"
    get_payment_proof.short_description = 'Comprobante'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completado')
        # Aquí también deberíamos actualizar la factura
        for payment in queryset:
            payment.invoice.status = 'pagada'
            payment.invoice.save()
        self.message_user(request, f'{updated} pagos marcados como completados (y facturas actualizadas).')
    mark_as_completed.short_description = 'Marcar como completado'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='fallido')
        # Y revertir la factura a 'pendiente'
        for payment in queryset:
            payment.invoice.status = 'pendiente' # O 'atrasada' si ya venció
            payment.invoice.save()
        self.message_user(request, f'{updated} pagos marcados como fallidos (y facturas revertidas).')
    mark_as_failed.short_description = 'Marcar como fallido'