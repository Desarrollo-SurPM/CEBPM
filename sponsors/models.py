from django.db import models

class Sponsor(models.Model):
    """Auspiciadores del club"""
    name = models.CharField(max_length=100, verbose_name='Nombre')
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True, verbose_name='Logo')
    url = models.URLField(blank=True, null=True, verbose_name='Sitio web')
    active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Auspiciador'
        verbose_name_plural = 'Auspiciadores'
        ordering = ['name']

    def __str__(self):
        return self.name