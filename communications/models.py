from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from players.models import Category # Importar Category

class BulkEmail(models.Model):
    """Correos masivos"""
    TYPE_CHOICES = [
        ('announcement', 'Anuncio'),
        ('notification', 'Notificación'),
        ('reminder', 'Recordatorio'),
        ('emergency', 'Emergencia'),
    ]
    AUDIENCE_CHOICES = [
        ('all_guardians', 'Todos los Apoderados'),
        ('team_guardians', 'Por Equipo'),
        ('specific_guardians', 'Apoderados Específicos'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviado'),
        ('scheduled', 'Programado'),
    ]

    title = models.CharField(max_length=200, verbose_name='Título')
    body_html = models.TextField(verbose_name='Contenido HTML')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Creado por')
    
    # --- CAMPOS NUEVOS Y MODIFICADOS ---
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='Estado')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='notification', verbose_name='Tipo de Mensaje')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, verbose_name='Audiencia')
    team = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Equipo Destino')
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='Enviado el')

    class Meta:
        verbose_name = 'Correo Masivo'
        verbose_name_plural = 'Correos Masivos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'

    # --- PROPIEDADES NUEVAS PARA ESTADÍSTICAS ---
    @property
    def total_recipients(self):
        return self.emailrecipient_set.count()

    @property
    def read_count(self):
        return self.emailrecipient_set.filter(read_at__isnull=False).count()

    @property
    def read_percentage(self):
        total = self.total_recipients
        if total == 0:
            return 0
        return (self.read_count / total) * 100

class EmailRecipient(models.Model):
    # ... (sin cambios en este modelo)
    """Destinatarios de correos masivos"""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    ]
    
    bulk_email = models.ForeignKey(BulkEmail, on_delete=models.CASCADE, verbose_name='Correo masivo')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='Enviado el')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado')
    error_message = models.TextField(blank=True, null=True, verbose_name='Mensaje de error')
    created_at = models.DateTimeField(auto_now_add=True)
    # --- CAMPO AÑADIDO ---
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Leído el')

    @property
    def is_read(self):
        return self.read_at is not None

    class Meta:
        verbose_name = 'Destinatario de Correo'
        verbose_name_plural = 'Destinatarios de Correo'
        unique_together = ['bulk_email', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.bulk_email.title} -> {self.user.email} ({self.get_status_display()})'