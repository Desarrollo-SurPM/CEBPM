from django.db import models

class Sponsor(models.Model):
    """
    Modelo para gestionar las empresas o entidades auspiciadoras.
    """
    name = models.CharField(max_length=100, verbose_name="Nombre Empresa")
    logo = models.ImageField(upload_to='sponsors/', blank=True, null=True, verbose_name="Logo")
    website = models.URLField(blank=True, null=True, verbose_name="Sitio Web")
    is_visible = models.BooleanField(default=True, verbose_name="Visible en la página web")
    
    # Datos de contacto del auspiciador (para gestión interna)
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Nombre de Contacto")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    contact_email = models.EmailField(blank=True, null=True, verbose_name="Email")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auspiciador"
        verbose_name_plural = "Auspiciadores"
        ordering = ['name']

    def __str__(self):
        return self.name