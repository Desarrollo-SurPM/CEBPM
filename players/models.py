from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """Categorías de jugadores"""
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def __str__(self):
        return self.name


class Player(models.Model):
    """Jugadores del club"""
    first_name = models.CharField(max_length=50, verbose_name='Nombre')
    last_name = models.CharField(max_length=50, verbose_name='Apellido')
    birthdate = models.DateField(verbose_name='Fecha de nacimiento')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    photo = models.ImageField(upload_to='players/', blank=True, null=True, verbose_name='Foto')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jugador'
        verbose_name_plural = 'Jugadores'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))


class GuardianPlayer(models.Model):
    """Relación entre apoderados y jugadores"""
    RELATION_CHOICES = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('tutor', 'Tutor/a'),
        ('abuelo', 'Abuelo/a'),
        ('otro', 'Otro'),
    ]
    
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Apoderado')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='Jugador')
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES, verbose_name='Relación')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Relación Apoderado-Jugador'
        verbose_name_plural = 'Relaciones Apoderado-Jugador'
        unique_together = ['guardian', 'player']

    def __str__(self):
        return f'{self.guardian.get_full_name()} - {self.player.get_full_name()} ({self.get_relation_display()})' 
