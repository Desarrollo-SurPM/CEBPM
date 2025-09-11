from django.db import models
from django.contrib.auth.models import User


class GuardianProfile(models.Model):
    """Perfil de apoderado vinculado al usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guardian_profile')
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    address = models.TextField(verbose_name='Dirección')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Apoderado'
        verbose_name_plural = 'Perfiles de Apoderados'

    def __str__(self):
        return f'{self.user.get_full_name()} - Apoderado'


class AdminProfile(models.Model):
    """Perfil de administrador vinculado al usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    position = models.CharField(max_length=100, verbose_name='Cargo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Administrador'
        verbose_name_plural = 'Perfiles de Administradores'

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.position}'
