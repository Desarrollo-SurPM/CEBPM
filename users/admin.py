from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import GuardianProfile, AdminProfile


class GuardianProfileInline(admin.StackedInline):
    model = GuardianProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Apoderado'
    fields = ('phone', 'address')
    extra = 0


class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Administrador'
    fields = ('position',)
    extra = 0
    

class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_user_type', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = ['activate_users', 'deactivate_users', 'send_welcome_email']
    
    def get_user_type(self, obj):
        if hasattr(obj, 'guardian_profile'):
            return 'Apoderado'
        elif hasattr(obj, 'admin_profile'):
            return 'Administrador'
        return 'Sin perfil'
    get_user_type.short_description = 'Tipo de Usuario'
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} usuario(s) activado(s) exitosamente.'
        )
    activate_users.short_description = 'Activar usuarios seleccionados'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} usuario(s) desactivado(s) exitosamente.'
        )
    deactivate_users.short_description = 'Desactivar usuarios seleccionados'
    
    def send_welcome_email(self, request, queryset):
        # Aquí se implementaría el envío de emails de bienvenida
        count = queryset.count()
        self.message_user(
            request,
            f'Email de bienvenida enviado a {count} usuario(s).'
        )
    send_welcome_email.short_description = 'Enviar email de bienvenida'


@admin.register(GuardianProfile)
class GuardianProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['send_notification']
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user',)
        }),
        ('Información del Apoderado', {
            'fields': ('phone', 'address')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def send_notification(self, request, queryset):
        # Aquí se implementaría el envío de notificaciones
        count = queryset.count()
        self.message_user(request, f'Notificación enviada a {count} apoderados.')
    send_notification.short_description = 'Enviar notificación'


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'created_at')
    list_filter = ('position', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'position')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('user',)
        }),
        ('Información del Administrador', {
            'fields': ('position',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


# Desregistrar el UserAdmin por defecto y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Personalizar el sitio de administración
admin.site.site_header = 'Administración - CEB FEM'
admin.site.site_title = 'Admin Club Deportes'
admin.site.index_title = 'Panel de Administración'
