from django.shortcuts import render
from django.http import JsonResponse
from .models import ClubHistory
from players.models import Player, Category
from schedules.models import Match, Activity
from finance.models import Sponsor
from django.utils import timezone
from datetime import datetime, timedelta


def landing_page(request):
    """Vista principal de la landing page"""
    context = {
        'recent_matches': Match.objects.filter(
            starts_at__gte=timezone.now()
        ).order_by('starts_at')[:3],
        'recent_activities': Activity.objects.filter(
            starts_at__gte=timezone.now()
        ).order_by('starts_at')[:3],
        'sponsors': Sponsor.objects.filter(active=True)[:6],
        'total_players': Player.objects.count(),
        'total_categories': Category.objects.count(),
    }
    return render(request, 'pages/landing.html', context)


def about_view(request):
    """Vista de la página Acerca de"""
    club_history = ClubHistory.objects.filter(published=True).order_by('-created_at')
    context = {
        'club_history': club_history
    }
    return render(request, 'pages/about.html', context)


def teams_view(request):
    """Vista de equipos y categorías"""
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories
    }
    return render(request, 'pages/teams.html', context)


def schedule_view(request):
    """Vista del calendario de partidos y actividades"""
    upcoming_matches = Match.objects.filter(
        starts_at__gte=timezone.now()
    ).order_by('starts_at')[:10]
    
    upcoming_activities = Activity.objects.filter(
        starts_at__gte=timezone.now()
    ).order_by('starts_at')[:10]
    
    context = {
        'upcoming_matches': upcoming_matches,
        'upcoming_activities': upcoming_activities
    }
    return render(request, 'pages/schedule.html', context)


def sponsors_view(request):
    """Vista de patrocinadores"""
    active_sponsors = Sponsor.objects.filter(active=True).order_by('name')
    context = {
        'sponsors': active_sponsors
    }
    return render(request, 'pages/sponsors.html', context)


def contact_view(request):
    """Vista de contacto"""
    if request.method == 'POST':
        # Aquí se podría implementar el envío de emails
        # Por ahora solo retornamos un mensaje de éxito
        return JsonResponse({
            'success': True,
            'message': 'Mensaje enviado correctamente. Te contactaremos pronto.'
        })
    
    return render(request, 'pages/contact.html')

