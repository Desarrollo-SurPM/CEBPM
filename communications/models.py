from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BulkEmail(models.Model):
    """
    Representa un mensaje masivo (noticia, notificación) enviado por un admin.
    """
    title = models.CharField(max_length=200, verbose_name="Título")
    body_html = models.TextField(verbose_name="Cuerpo del Mensaje (HTML)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NUEVO CAMPO ---
    attachment = models.FileField(
        upload_to='communications_attachments/', 
        blank=True, 
        null=True, 
        verbose_name="Adjuntar Archivo"
    )
    # --- FIN NUEVO CAMPO ---

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mensaje Masivo"
        verbose_name_plural = "Mensajes Masivos"


class EmailRecipient(models.Model):
    """
    Registra qué usuario recibió qué mensaje masivo.
    """
    bulk_email = models.ForeignKey(BulkEmail, on_delete=models.CASCADE, related_name="recipients")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    status = models.CharField(max_length=20, default='pendiente') # ej: enviado, fallido
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True) # <-- Este campo ya existe

    def __str__(self):
        return f"{self.user.username} - {self.bulk_email.title}"

    class Meta:
        unique_together = ['bulk_email', 'user'] # Evita enviar el mismo mensaje dos veces
        ordering = ['-sent_at']