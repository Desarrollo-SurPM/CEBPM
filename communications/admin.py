from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Q
from .models import BulkEmail, EmailRecipient


@admin.register(BulkEmail)
class BulkEmailAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'recipient_count', 'sent_count', 'status_badge', 'created_at')
    list_filter = ('is_sent', 'created_at', 'sent_at')
    search_fields = ('title', 'body_html', 'created_by__first_name', 'created_by__last_name')
    readonly_fields = ('sent_at', 'created_at', 'recipient_count', 'sent_count')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información del Correo', {
            'fields': ('title', 'body_html', 'created_by')
        }),
        ('Estado', {
            'fields': ('is_sent', 'sent_at')
        }),
        ('Estadísticas', {
            'fields': ('recipient_count', 'sent_count'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def sender_info(self, obj):
        if obj.sender:
            return f"{obj.sender.first_name} {obj.sender.last_name}"
        return 'Sistema'
    sender_info.short_description = 'Remitente'
    
    def recipient_info(self, obj):
        return f"{obj.recipient.first_name} {obj.recipient.last_name}"
    recipient_info.short_description = 'Destinatario'
    
    def status_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✅ Leído</span>'
            )
        else:
            days_ago = (timezone.now().date() - obj.sent_at.date()).days if obj.sent_at else 0
            if days_ago > 7:
                color = '#dc3545'  # Red for old unread
                icon = '🔴'
            elif days_ago > 3:
                color = '#ffc107'  # Yellow for moderately old
                icon = '🟡'
            else:
                color = '#17a2b8'  # Blue for recent
                icon = '🔵'
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{} No leído</span>',
                color, icon
            )
    status_badge.short_description = 'Estado'
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_bulk_message']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} mensajes marcados como leídos.')
    mark_as_read.short_description = 'Marcar como leído'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} mensajes marcados como no leídos.')
    mark_as_unread.short_description = 'Marcar como no leído'
    
    def send_bulk_message(self, request, queryset):
        # This would open a form to send bulk messages
        self.message_user(request, 'Función de envío masivo disponible en desarrollo.')
    send_bulk_message.short_description = 'Enviar mensaje masivo'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Add annotations for better performance
        return qs.select_related('sender', 'recipient')


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('bulk_email', 'user', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'sent_at', 'created_at')
    search_fields = ('bulk_email__title', 'user__first_name', 'user__last_name')
    readonly_fields = ('sent_at', 'created_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información de la Notificación', {
            'fields': ('user', 'title', 'message')
        }),
        ('Configuración', {
            'fields': ('notification_type', 'priority')
        }),
        ('Estado', {
            'fields': ('is_read', 'read_at')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_info(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_info.short_description = 'Usuario'
    
    def priority_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        icons = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'urgent': '🔴'
        }
        color = colors.get(obj.priority, '#6c757d')
        icon = icons.get(obj.priority, '⚪')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{} {}</span>',
            color, icon, obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_old_notifications']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notificaciones marcadas como leídas.')
    mark_as_read.short_description = 'Marcar como leída'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notificaciones marcadas como no leídas.')
    mark_as_unread.short_description = 'Marcar como no leída'
    
    def delete_old_notifications(self, request, queryset):
        # Delete notifications older than 30 days
        old_date = timezone.now() - timezone.timedelta(days=30)
        old_notifications = queryset.filter(created_at__lt=old_date, is_read=True)
        count = old_notifications.count()
        old_notifications.delete()
        self.message_user(request, f'{count} notificaciones antiguas eliminadas.')
    delete_old_notifications.short_description = 'Eliminar notificaciones antiguas'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
