from django.db import models


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
