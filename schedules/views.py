# schedules/views.py

from django.shortcuts import render
from django.utils import timezone
from .models import Match, Activity

def schedule_list_view(request):
    """
    Muestra una lista pública de los próximos partidos y actividades.
    """
    today = timezone.now()
    
    upcoming_matches = Match.objects.filter(starts_at__gte=today).order_by('starts_at')
    upcoming_activities = Activity.objects.filter(starts_at__gte=today).order_by('starts_at')

    context = {
        'upcoming_matches': upcoming_matches,
        'upcoming_activities': upcoming_activities,
    }
    return render(request, 'schedules/schedule_list.html', context)