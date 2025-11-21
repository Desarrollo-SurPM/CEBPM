from django.utils import timezone
from django.db import models

class LandingNews(models.Model):
    """Noticias para la landing page"""
    image = models.ImageField(upload_to='landing/news/', blank=False, null=False, verbose_name="Imagen (Obligatoria)")
    tag = models.CharField(max_length=50, blank=True, null=True, verbose_name="Etiqueta (Ej: PLAYOFF)")
    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Párrafo")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")

    class Meta:
        verbose_name = "Noticia de Landing"
        verbose_name_plural = "Noticias de Landing (Máx. 3 se muestran)"
        ordering = ['-created_at'] # Las más nuevas primero

    def __str__(self):
        return self.title

class LandingEvent(models.Model):
    """Eventos para el calendario de la landing page"""
    EVENT_TYPE_CHOICES = [
        ('partido', 'Partido'),
        ('novedad', 'Novedad'),
        ('reunion', 'Reunión'),
        ('evento', 'Evento'),
    ]

    title = models.CharField(max_length=200, verbose_name="Título del Evento")
    date = models.DateTimeField(verbose_name="Fecha y Hora")
    event_type = models.CharField(
        max_length=10, 
        choices=EVENT_TYPE_CHOICES, 
        default='novedad',
        verbose_name="Tipo de Evento"
    )

    class Meta:
        verbose_name = "Evento de Landing"
        verbose_name_plural = "Eventos del Calendario (Landing)"
        ordering = ['date'] # Los más próximos primero

    def __str__(self):
        return f"[{self.get_event_type_display()}] {self.title} - {self.date.strftime('%d/%m/%Y %H:%M')}"
class ClubHistory(models.Model):
    """Historia del club"""
    title = models.CharField(max_length=200, verbose_name='Título')
    body_html = models.TextField(verbose_name='Contenido HTML')
    published = models.BooleanField(default=False, verbose_name='Publicado')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historia del Club'
        verbose_name_plural = 'Historias del Club'
        ordering = ['-created_at']

    def __str__(self):
        status = 'Publicado' if self.published else 'Borrador'
        return f'{self.title} ({status})' 
