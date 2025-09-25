from django.contrib import admin
from django.utils.html import format_html
from .models import Sponsor

@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'logo_preview', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'url']
    ordering = ['name']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'logo', 'url', 'active')
        }),
    )
    
    actions = ['activate_sponsors', 'deactivate_sponsors']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.logo.url)
        return 'Sin logo'
    logo_preview.short_description = 'Logo'
    
    def activate_sponsors(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} auspiciadores activados.')
    activate_sponsors.short_description = 'Activar auspiciadores'
    
    def deactivate_sponsors(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} auspiciadores desactivados.')
    deactivate_sponsors.short_description = 'Desactivar auspiciadores'