from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import BulkEmail, EmailRecipient

@admin.register(BulkEmail)
class BulkEmailAdmin(admin.ModelAdmin):
    # --- CORREGIDO: Usando los nuevos campos y propiedades ---
    list_display = ('title', 'created_by', 'total_recipients', 'read_count', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'sent_at', 'message_type', 'audience')
    search_fields = ('title', 'body_html', 'created_by__first_name', 'created_by__last_name')
    # Usamos las propiedades del modelo que ahora sí existen
    readonly_fields = ('sent_at', 'created_at', 'total_recipients', 'read_count', 'read_percentage')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Correo', {
            'fields': ('title', 'body_html', 'created_by', 'message_type', 'audience', 'team')
        }),
        ('Estado', {
            'fields': ('status', 'sent_at')
        }),
        ('Estadísticas', {
            'fields': ('total_recipients', 'read_count', 'read_percentage'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['send_bulk_message']

    def send_bulk_message(self, request, queryset):
        # Aquí se implementaría el envío de emails de bienvenida
        count = queryset.count()
        self.message_user(
            request,
            f'Funcionalidad de envío masivo para {count} correos pendiente de implementación.'
        )
    send_bulk_message.short_description = 'Enviar correos seleccionados'

@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    # --- CORREGIDO: Adaptado a los campos reales del modelo ---
    list_display = ('bulk_email', 'user_info', 'status', 'sent_at', 'is_read_display', 'created_at')
    list_filter = ('status', 'sent_at', 'created_at', 'read_at')
    search_fields = ('bulk_email__title', 'user__first_name', 'user__last_name')
    readonly_fields = ('sent_at', 'created_at', 'read_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Envío', {
            'fields': ('bulk_email', 'user', 'status', 'error_message')
        }),
        ('Fechas', {
            'fields': ('sent_at', 'read_at', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_info(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_info.short_description = 'Usuario'
    
    def is_read_display(self, obj):
        if obj.read_at:
            return format_html('<span style="color: green;">✔ Leído</span>')
        return format_html('<span style="color: red;">✖ No Leído</span>')
    is_read_display.short_description = 'Estado de Lectura'
    
    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(read_at=timezone.now())
        self.message_user(request, f'{updated} mensajes marcados como leídos.')
    mark_as_read.short_description = 'Marcar como leído'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(read_at=None)
        self.message_user(request, f'{updated} mensajes marcados como no leídos.')
    mark_as_unread.short_description = 'Marcar como no leído'