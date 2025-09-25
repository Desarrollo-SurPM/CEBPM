# players/views.py

from django.shortcuts import render
from .models import Player, Category

def player_roster_view(request):
    """
    Muestra un listado público de jugadores, filtrado por categoría.
    """
    categories = Category.objects.all()
    selected_category_id = request.GET.get('category')

    if selected_category_id:
        players = Player.objects.filter(category_id=selected_category_id, status='active').order_by('last_name')
        selected_category = Category.objects.get(id=selected_category_id)
    else:
        players = Player.objects.none() # No mostrar jugadores si no se selecciona categoría
        selected_category = None

    context = {
        'categories': categories,
        'selected_category': selected_category,
        'players': players,
    }
    return render(request, 'players/player_roster.html', context)