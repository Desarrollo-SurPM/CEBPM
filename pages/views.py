from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from .models import ClubHistory, LandingNews, LandingEvent
from players.models import Player, Category
from schedules.models import Match, Activity
from sponsors.models import Sponsor  # Importante

def landing_page(request):
    """Vista principal de la landing page"""
    context = {
        'recent_matches': Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:3],
        'recent_activities': Activity.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:3],
        
        # --- CORRECCIÓN: is_visible=True ---
        'sponsors': Sponsor.objects.filter(is_visible=True)[:6],
        
        'total_players': Player.objects.count(),
        'total_categories': Category.objects.count(),
        'latest_news': LandingNews.objects.all()[:3],
        'upcoming_events': LandingEvent.objects.filter(date__gte=timezone.now()).order_by('date')[:5],
        'featured_players': Player.objects.filter(is_featured=True)[:4],
    }
    return render(request, 'pages/landing.html', context)

def about_view(request):
    club_history = ClubHistory.objects.filter(published=True).order_by('-created_at')
    return render(request, 'pages/about.html', {'club_history': club_history})

def teams_view(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'pages/teams.html', {'categories': categories})

def schedule_view(request):
    upcoming_matches = Match.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:10]
    upcoming_activities = Activity.objects.filter(starts_at__gte=timezone.now()).order_by('starts_at')[:10]
    return render(request, 'pages/schedule.html', {'upcoming_matches': upcoming_matches, 'upcoming_activities': upcoming_activities})

def sponsors_view(request):
    # --- CORRECCIÓN: is_visible=True ---
    active_sponsors = Sponsor.objects.filter(is_visible=True).order_by('name')
    return render(request, 'pages/sponsors.html', {'sponsors': active_sponsors})

def contact_view(request):
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Mensaje enviado correctamente.'})
    return render(request, 'pages/contact.html')