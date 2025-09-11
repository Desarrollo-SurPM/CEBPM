from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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


class Registration(models.Model):
    """Player registration requests"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
    ]
    
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Apoderado')
    player_first_name = models.CharField(max_length=50, verbose_name='Nombre del jugador')
    player_last_name = models.CharField(max_length=50, verbose_name='Apellido del jugador')
    player_rut = models.CharField(max_length=12, verbose_name='RUT del jugador')
    player_birth_date = models.DateField(verbose_name='Fecha de nacimiento')
    team = models.CharField(max_length=50, verbose_name='Equipo solicitado')
    emergency_contact = models.CharField(max_length=100, verbose_name='Contacto de emergencia')
    emergency_phone = models.CharField(max_length=20, verbose_name='Teléfono de emergencia')
    medical_info = models.TextField(blank=True, verbose_name='Información médica')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Estado')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_registrations', verbose_name='Aprobado por')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de aprobación')
    rejection_reason = models.TextField(blank=True, verbose_name='Motivo de rechazo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Registro de Jugador'
        verbose_name_plural = 'Registros de Jugadores'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.player_first_name} {self.player_last_name} - {self.get_status_display()}'
    
    @property
    def first_name(self):
        return self.player_first_name
    
    @property
    def last_name(self):
        return self.player_last_name
    
    @property
    def birth_date(self):
        return self.player_birth_date
