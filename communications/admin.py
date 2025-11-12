from django.contrib import admin
from .models import BulkEmail, EmailRecipient

@admin.register(BulkEmail)
class BulkEmailAdmin(admin.ModelAdmin):
    """
    Admin para el modelo BulkEmail.
    """
    # --- CORREGIDO ---
    # 1. 'recipient_count' y 'sent_count' no son campos, son métodos (los añadimos abajo).
    # 2. Añadido 'attachment' que sí existe.
    list_display = ['title', 'is_sent', 'recipient_count', 'sent_count', 'sent_at', 'attachment']
    list_filter = ['is_sent', 'sent_at']
    search_fields = ['title', 'body_html']
    
    # --- CORREGIDO ---
    # 3. 'recipient_count' y 'sent_count' son readonly porque son métodos.
    readonly_fields = ['created_by', 'sent_at', 'recipient_count', 'sent_count']
    
    fieldsets = (
        ('Información', {
            'fields': ('title', 'body_html', 'attachment')
        }),
        ('Estado (Automático)', {
            'fields': ('is_sent', 'sent_at', 'created_by', 'recipient_count', 'sent_count')
        }),
    )

    # --- MÉTODOS AÑADIDOS ---
    # 4. Funciones para calcular los conteos que sí queríamos mostrar.
    def recipient_count(self, obj):
        return obj.recipients.count()
    recipient_count.short_description = 'Destinatarios'

    def sent_count(self, obj):
        # Asumiendo que 'enviado' es un estado válido
        return obj.recipients.filter(status='enviado').count()
    sent_count.short_description = 'Enviados'
    # --- FIN MÉTODOS ---


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    """
    Admin para el modelo EmailRecipient.
    """
    # --- CORREGIDO ---
    # 1. 'created_at' no existe en el modelo, usamos 'read_at' en su lugar.
    list_display = ['user', 'bulk_email', 'status', 'sent_at', 'read_at']
    
    # 2. 'created_at' no existe, usamos 'sent_at' y 'read_at'.
    list_filter = ['status', 'sent_at', 'read_at']
    search_fields = ['user__username', 'user__email', 'bulk_email__title']
    
    # 3. 'created_at' no existe. 'sent_at' y 'read_at' son los correctos.
    readonly_fields = ['user', 'bulk_email', 'sent_at', 'read_at']
    
    # 4. 'created_at' no existe, usamos 'sent_at' (que sí es un DateTimeField).
    date_hierarchy = 'sent_at'