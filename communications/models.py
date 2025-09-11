from django.db import models
from django.contrib.auth.models import User


class BulkEmail(models.Model):
    """Correos masivos"""
    title = models.CharField(max_length=200, verbose_name='Título')
    body_html = models.TextField(verbose_name='Contenido HTML')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Creado por')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='Enviado el')
    is_sent = models.BooleanField(default=False, verbose_name='Enviado')

    class Meta:
        verbose_name = 'Correo Masivo'
        verbose_name_plural = 'Correos Masivos'
        ordering = ['-created_at']

    def __str__(self):
        status = 'Enviado' if self.is_sent else 'Borrador'
        return f'{self.title} ({status})'

    @property
    def recipient_count(self):
        return self.emailrecipient_set.count()

    @property
    def sent_count(self):
        return self.emailrecipient_set.filter(sent_at__isnull=False).count()


class EmailRecipient(models.Model):
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

    class Meta:
        verbose_name = 'Destinatario de Correo'
        verbose_name_plural = 'Destinatarios de Correo'
        unique_together = ['bulk_email', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.bulk_email.title} -> {self.user.email} ({self.get_status_display()})' 
