from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import Category, Player, GuardianPlayer


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_player_count', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    
    def get_player_count(self, obj):
        count = obj.player_set.filter(is_active=True).count()
        return f'{count} jugadores'
    get_player_count.short_description = 'Jugadores Activos'


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'get_full_name', 'category', 'get_age', 'is_active', 'created_at'
    )
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name')
    ordering = ('last_name', 'first_name')
    actions = ['activate_players', 'deactivate_players']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'birthdate', 'photo')
        }),
        ('Información Deportiva', {
            'fields': ('category', 'is_active')
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    get_full_name.short_description = 'Nombre Completo'
    get_full_name.admin_order_field = 'last_name'
    
    def get_age(self, obj):
        return f'{obj.age} años'
    get_age.short_description = 'Edad'
    
    def activate_players(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} jugadores activados exitosamente.')
    activate_players.short_description = 'Activar jugadores seleccionados'
    
    def deactivate_players(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} jugadores desactivados exitosamente.')
    deactivate_players.short_description = 'Desactivar jugadores seleccionados'


@admin.register(GuardianPlayer)
class GuardianPlayerAdmin(admin.ModelAdmin):
    list_display = ('guardian', 'player', 'relation', 'created_at')
    list_filter = ('relation', 'created_at')
    search_fields = (
        'guardian__first_name', 'guardian__last_name',
        'player__first_name', 'player__last_name'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Relación', {
            'fields': ('guardian', 'player', 'relation')
        }),
    )
    
    readonly_fields = ('created_at',)
