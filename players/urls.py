from django.urls import path
from . import views

app_name = 'players'
urlpatterns = [
    path('roster/', views.player_roster_view, name='player_roster'),
]