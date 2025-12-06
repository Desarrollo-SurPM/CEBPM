from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from itertools import chain
from operator import attrgetter

# Modelos
from .models import ClubHistory, LandingNews
from players.models import Category
from schedules.models import Match, Activity
from sponsors.models import Sponsor

# =========================================================
# VISTA: LANDING PAGE (Inicio)
# =========================================================
def landing_page(request):
    """
    Muestra la página de inicio con:
    - Próximos eventos mezclados (Partidos + Entrenamientos) ordenados por fecha.
    - Últimas noticias.
    - Auspiciadores.
    """
    today = timezone.now()
    
    # 1. Obtener Partidos Futuros
    upcoming_matches = Match.objects.filter(starts_at__gte=today).select_related('category').order_by('starts_at')
    
    # 2. Obtener Actividades/Entrenamientos Futuros
    upcoming_activities = Activity.objects.filter(starts_at__gte=today).select_related('category').order_by('starts_at')
    
    # 3. Unificarlos en una sola lista cronológica para la sección "Próximos Encuentros" del Home
    upcoming_events = sorted(
        chain(upcoming_matches, upcoming_activities),
        key=attrgetter('starts_at')
    )[:6] # Limitamos a los próximos 6 eventos

    context = {
        'upcoming_events': upcoming_events,
        'latest_news': LandingNews.objects.all().order_by('-created_at')[:3],
        'sponsors': Sponsor.objects.filter(is_visible=True),
    }
    return render(request, 'pages/landing.html', context)

# =========================================================
# VISTA: CALENDARIO (Schedule)
# =========================================================
def schedule(request):
    """
    Vista pública del calendario detallado (/pages/calendario/).
    Muestra partidos, entrenamientos y actividades en SECCIONES SEPARADAS.
    Permite filtrar por categoría mediante ?category=ID.
    """
    today = timezone.now()
    category_id = request.GET.get('category')
    
    # 1. Consultas Base (Desde hoy en adelante)
    matches = Match.objects.filter(starts_at__gte=today).select_related('category').order_by('starts_at')
    trainings = Activity.objects.filter(starts_at__gte=today, type='entrenamiento').select_related('category').order_by('starts_at')
    activities = Activity.objects.filter(starts_at__gte=today, type='otro').select_related('category').order_by('starts_at')
    
    # 2. Lógica de Filtrado
    current_category = None
    selected_cat_id = None

    if category_id and category_id != 'all':
        try:
            current_category = Category.objects.get(id=category_id)
            selected_cat_id = current_category.id
            
            # Filtramos cada lista por la categoría seleccionada
            matches = matches.filter(category=current_category)
            trainings = trainings.filter(category=current_category)
            activities = activities.filter(category=current_category)
            
        except (Category.DoesNotExist, ValueError):
            pass # Si el ID es inválido, mostramos todo sin filtrar

    context = {
        'matches': matches,       # Sección "Próximos Partidos"
        'trainings': trainings,   # Sección "Entrenamientos"
        'activities': activities, # Sección "Actividades Especiales"
        'categories': Category.objects.all().order_by('name'), # Para el dropdown de filtros
        'current_category': current_category,
        'selected_cat_id': selected_cat_id,
        'page_title': 'Calendario Oficial'
    }
    return render(request, 'pages/schedule.html', context)

# =========================================================
# OTRAS VISTAS (Estáticas y Sponsors)
# =========================================================

def about_view(request):
    """Historia y Quiénes Somos"""
    club_history = ClubHistory.objects.filter(published=True).order_by('-created_at')
    return render(request, 'pages/about.html', {'club_history': club_history})

def teams_view(request):
    """Listado de Categorías/Equipos"""
    categories = Category.objects.all().order_by('name')
    return render(request, 'pages/teams.html', {'categories': categories})

def sponsors_view(request):
    """Listado de Auspiciadores"""
    active_sponsors = Sponsor.objects.filter(is_visible=True).order_by('name')
    return render(request, 'pages/sponsors.html', {'sponsors': active_sponsors})

def contact_view(request):
    """Página de Contacto"""
    if request.method == 'POST':
        return JsonResponse({'success': True, 'message': 'Mensaje enviado correctamente.'})
    return render(request, 'pages/contact.html')