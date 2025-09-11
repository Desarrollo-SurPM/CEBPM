from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Match, Activity, Birthday


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('title', 'opponent', 'starts_at', 'location', 'category')
    list_filter = ('category', 'starts_at')
    search_fields = ('title', 'opponent', 'location')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'starts_at'
    
    fieldsets = (
        ('Información del Partido', {
            'fields': ('title', 'category', 'opponent', 'starts_at', 'location')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    # Methods removed due to model field changes
    # def match_info(self, obj):
    #     home_away = '🏠' if obj.is_home else '✈️'
    #     return f"{obj.team.name} {home_away} vs {obj.opponent}"
    # match_info.short_description = 'Partido'
    # 
    # def status_badge(self, obj):
    #     colors = {
    #         'scheduled': '#17a2b8',
    #         'in_progress': '#ffc107',
    #         'completed': '#28a745',
    #         'cancelled': '#dc3545',
    #         'postponed': '#6c757d'
    #     }
    #     color = colors.get(obj.status, '#6c757d')
    #     return format_html(
    #         '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
    #         color, obj.get_status_display()
     # )
     # status_badge.short_description = 'Estado'
    
     # Methods commented out due to model field changes
     # def result_display(self, obj):
     #     if obj.status == 'completed' and obj.goals_for is not None and obj.goals_against is not None:
     #         if obj.goals_for > obj.goals_against:
     #             result_class = 'success'
     #             icon = '🏆'
     #         elif obj.goals_for < obj.goals_against:
     #             result_class = 'danger'
     #             icon = '😞'
     #         else:
     #             result_class = 'warning'
     #             icon = '🤝'
     #         return format_html(
     #             '<span class="badge badge-{}">{}  {}-{}</span>',
     #             result_class, icon, obj.goals_for, obj.goals_against
     #         )
     #     return '-'
     # result_display.short_description = 'Resultado'
     # 
     # actions = ['mark_as_completed', 'mark_as_cancelled', 'mark_as_in_progress']
     # 
     # def mark_as_completed(self, request, queryset):
     #     updated = queryset.update(status='completed')
     #     self.message_user(request, f'{updated} partidos marcados como completados.')
     # mark_as_completed.short_description = 'Marcar como completado'
     # 
     # def mark_as_cancelled(self, request, queryset):
     #     updated = queryset.update(status='cancelled')
     #     self.message_user(request, f'{updated} partidos cancelados.')
     # mark_as_cancelled.short_description = 'Cancelar partidos'
     # 
     # def mark_as_in_progress(self, request, queryset):
     #     updated = queryset.update(status='in_progress')
     #     self.message_user(request, f'{updated} partidos marcados en progreso.')
     # mark_as_in_progress.short_description = 'Marcar en progreso'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'starts_at', 'ends_at', 'location', 'duration_display']
    list_filter = ['type', 'starts_at', 'created_at']
    search_fields = ['title', 'location', 'description']
    date_hierarchy = 'starts_at'
    ordering = ['-starts_at']
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('title', 'type', 'location')
        }),
        ('Horario', {
            'fields': ('starts_at', 'ends_at')
        }),
        ('Detalles', {
            'fields': ('description',)
        })
    )
    
    actions = ['mark_as_training', 'mark_as_other']
    
    def duration_display(self, obj):
        if obj.duration:
            return str(obj.duration)
        return 'N/A'
    duration_display.short_description = 'Duración'
    
    def mark_as_training(self, request, queryset):
        updated = queryset.update(type='entrenamiento')
        self.message_user(request, f'{updated} actividades marcadas como entrenamientos.')
    mark_as_training.short_description = 'Marcar como entrenamiento'
    
    def mark_as_other(self, request, queryset):
        updated = queryset.update(type='otro')
        self.message_user(request, f'{updated} actividades marcadas como otro tipo.')
    mark_as_other.short_description = 'Marcar como otro tipo'


@admin.register(Birthday)
class BirthdayAdmin(admin.ModelAdmin):
    list_display = ['get_player_name', 'date', 'age_display', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['player__first_name', 'player__last_name']
    date_hierarchy = 'date'
    ordering = ['date']
    
    fieldsets = (
        ('Información del Cumpleaños', {
            'fields': ('player', 'date')
        }),
    )
    
    def get_player_name(self, obj):
        return f"{obj.player.first_name} {obj.player.last_name}"
    get_player_name.short_description = 'Jugador'
    get_player_name.admin_order_field = 'player__first_name'
    
    def age_display(self, obj):
        from datetime import date
        today = date.today()
        age = today.year - obj.date.year - ((today.month, today.day) < (obj.date.month, obj.date.day))
        return f"{age} años"
    age_display.short_description = 'Edad'
