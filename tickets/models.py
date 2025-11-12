from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    """
    Representa una solicitud o consulta de un apoderado.
    """
    STATUS_CHOICES = [
        ('abierto', 'Abierto'),
        ('respondido', 'Respondido por Admin'),
        ('cerrado', 'Cerrado'),
    ]

    subject = models.CharField(max_length=200, verbose_name="Asunto")
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Apoderado")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='abierto', verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ticket de Soporte"
        verbose_name_plural = "Tickets de Soporte"
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject} ({self.guardian.username})"

class TicketReply(models.Model):
    """
    Representa un mensaje (respuesta) dentro de un ticket.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="replies", verbose_name="Ticket")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario") # Puede ser admin o apoderado
    message = models.TextField(verbose_name="Mensaje")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Respuesta de Ticket"
        verbose_name_plural = "Respuestas de Tickets"
        ordering = ['created_at'] # Las más antiguas primero para leer en orden

    def __str__(self):
        return f"Respuesta de {self.user.username} en Ticket #{self.ticket.id}"