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
    list_display = ['get_guardian_name', 'get_player_name', 'amount', 'due_date', 'status', 'is_overdue_display']
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
    
    actions = ['mark_as_paid', 'mark_as_overdue']
    
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
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Vencida</span>')
        return 'Al día'
    is_overdue_display.short_description = 'Estado de vencimiento'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='pagada')
        self.message_user(request, f'{updated} facturas marcadas como pagadas.')
    mark_as_paid.short_description = 'Marcar como pagada'
    
    def mark_as_overdue(self, request, queryset):
        updated = queryset.update(status='atrasada')
        self.message_user(request, f'{updated} facturas marcadas como atrasadas.')
    mark_as_overdue.short_description = 'Marcar como atrasada'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['get_invoice_info', 'amount', 'paid_at', 'method', 'status', 'transaction_id']
    list_filter = ['status', 'method', 'paid_at', 'created_at']
    search_fields = ['invoice__guardian__first_name', 'invoice__guardian__last_name', 'transaction_id']
    date_hierarchy = 'paid_at'
    ordering = ['-paid_at']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('invoice', 'amount', 'paid_at', 'method')
        }),
        ('Estado y Transacción', {
            'fields': ('status', 'transaction_id')
        })
    )
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def get_invoice_info(self, obj):
        return f"Factura #{obj.invoice.id} - {obj.invoice.guardian.first_name} {obj.invoice.guardian.last_name}"
    get_invoice_info.short_description = 'Factura'
    get_invoice_info.admin_order_field = 'invoice__id'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completado')
        self.message_user(request, f'{updated} pagos marcados como completados.')
    mark_as_completed.short_description = 'Marcar como completado'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='fallido')
        self.message_user(request, f'{updated} pagos marcados como fallidos.')
    mark_as_failed.short_description = 'Marcar como fallido'