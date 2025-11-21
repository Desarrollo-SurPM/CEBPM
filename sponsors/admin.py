from django.contrib import admin
from django.utils.html import format_html
from .models import Sponsor

@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    # Usar los nombres nuevos: is_visible y website
    list_display = ['name', 'is_visible', 'logo_preview', 'created_at']
    list_filter = ['is_visible', 'created_at']
    search_fields = ['name', 'website']
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.logo.url)
        return 'Sin logo'