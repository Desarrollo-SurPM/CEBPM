from django.db import models
from players.models import Category, Player


class Match(models.Model):
    """Partidos del club"""
    title = models.CharField(max_length=200, verbose_name='Título')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    opponent = models.CharField(max_length=100, verbose_name='Rival')
    location = models.CharField(max_length=200, verbose_name='Ubicación')
    starts_at = models.DateTimeField(verbose_name='Fecha y hora de inicio')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Partido'
        verbose_name_plural = 'Partidos'
        ordering = ['starts_at']

    def __str__(self):
        return f'{self.title} - {self.category.name} vs {self.opponent}'

    @property
    def is_upcoming(self):
        from datetime import datetime
        return self.starts_at > datetime.now()


class Activity(models.Model):
    """Actividades del club"""
    TYPE_CHOICES = [
        ('entrenamiento', 'Entrenamiento'),
        ('otro', 'Otro'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Título')
    location = models.CharField(max_length=200, verbose_name='Ubicación')
    starts_at = models.DateTimeField(verbose_name='Fecha y hora de inicio')
    ends_at = models.DateTimeField(verbose_name='Fecha y hora de fin')
    type = models.CharField(max_length=15, choices=TYPE_CHOICES, verbose_name='Tipo')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['starts_at']

    def __str__(self):
        return f'{self.title} - {self.get_type_display()}'

    @property
    def is_upcoming(self):
        from datetime import datetime
        return self.starts_at > datetime.now()

    @property
    def duration(self):
        return self.ends_at - self.starts_at


class Birthday(models.Model):
    """Cumpleaños de jugadores"""
    player = models.OneToOneField(Player, on_delete=models.CASCADE, verbose_name='Jugador')
    date = models.DateField(verbose_name='Fecha de cumpleaños')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cumpleaños'
        verbose_name_plural = 'Cumpleaños'
        ordering = ['date']

    def __str__(self):
        return f'Cumpleaños de {self.player.get_full_name()} - {self.date.strftime("%d/%m")}'
