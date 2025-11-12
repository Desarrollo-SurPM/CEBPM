from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    # ... (tu modelo Category no cambia) ...
    name = models.CharField(max_length=50, unique=True, verbose_name='Nombre')
    is_registration_open = models.BooleanField(
        default=False, 
        verbose_name='Inscripciones Abiertas',
        help_text='Marcar si esta categoría acepta nuevas inscripciones desde la web.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']
    def __str__(self):
        return self.name


# ==============================================
# INICIO DE LA CLASE PLAYER MODIFICADA
# ==============================================
class Player(models.Model):
    """Jugadores del club"""
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('injured', 'Lesionado'),
    ]
    
    POSITION_CHOICES = [
        ('base', 'Base'),
        ('escolta', 'Escolta'),
        ('alero', 'Alero'),
        ('ala_pivot', 'Ala-Pívot'),
        ('pivot', 'Pívot'),
    ]

    # --- DATOS PERSONALES (la mayoría ya estaban) ---
    first_name = models.CharField(max_length=50, verbose_name='Nombre')
    last_name = models.CharField(max_length=50, verbose_name='Apellido')
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='Apodo')
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, verbose_name='RUT')
    birthdate = models.DateField(verbose_name='Fecha de nacimiento')
    photo = models.ImageField(upload_to='players/', blank=True, null=True, verbose_name='Foto')
    
    # --- NUEVOS DATOS DE CONTACTO JUGADORA ---
    player_email = models.EmailField(max_length=100, blank=True, null=True, verbose_name='Email Jugadora')
    player_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono Jugadora')

    # --- DATOS DEPORTIVOS ---
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Categoría')
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True, null=True, verbose_name='Posición')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name='Estado')
    
    # --- NUEVOS DATOS DEPORTIVOS/TÉCNICOS ---
    height = models.DecimalField(
        max_digits=5, decimal_places=2, 
        blank=True, null=True, 
        verbose_name='Estatura (cm)',
        help_text="Ej: 170.5"
    )
    association = models.CharField(
        max_length=100, 
        blank=True, null=True, 
        verbose_name='Asociación/Federación',
        help_text="Ej: Federación de Básquetbol de Chile"
    )

    # --- NUEVOS DATOS DE SALUD Y PERMISOS ---
    medical_conditions = models.TextField(
        blank=True, null=True, 
        verbose_name='Condiciones Médicas',
        help_text="Alergias, condiciones pre-existentes, lesiones anteriores, etc."
    )
    permissions_notes = models.TextField(
        blank=True, null=True, 
        verbose_name='Permisos y Autorizaciones',
        help_text="Notas sobre permisos de imagen, autorizaciones de viaje, etc."
    )

    # --- Campos Internos ---
    is_featured = models.BooleanField(default=False, verbose_name='¿Jugadora Destacada? (Landing)')
    created_at = models.DateTimeField(auto_now_add=True) # Fecha de inscripción
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jugador'
        verbose_name_plural = 'Jugadores'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        if self.nickname:
            return f'{self.first_name} "{self.nickname}" {self.last_name}'
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        if not self.birthdate:
            return None
        today = timezone.now().date()
        return today.year - self.birthdate.year - ((today.month, today.day) < (self.birthdate.month, self.birthdate.day))
# ==============================================
# FIN DE LA CLASE PLAYER MODIFICADA
# ==============================================
class PlayerDocument(models.Model):
    """
    Almacena documentos adjuntos para una jugadora (permisos, certificados, etc.)
    """
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name="documents",
        verbose_name="Jugadora"
    )
    title = models.CharField(max_length=150, verbose_name="Título del Documento")
    file = models.FileField(upload_to='player_documents/', verbose_name="Archivo")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Subida")
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Subido por"
    )

    class Meta:
        verbose_name = "Documento de Jugadora"
        verbose_name_plural = "Documentos de Jugadora"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.player.get_full_name()})"

class GuardianPlayer(models.Model):
    # ... (tu modelo GuardianPlayer no cambia) ...
    RELATION_CHOICES = [
        ('padre', 'Padre'),
        ('madre', 'Madre'),
        ('tutor', 'Tutor/a'),
        ('abuelo', 'Abuelo/a'),
        ('otro', 'Otro'),
    ]
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Apoderado')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='Jugador')
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES, verbose_name='Relación')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = 'Relación Apoderado-Jugador'
        verbose_name_plural = 'Relaciones Apoderado-Jugador'
        unique_together = ['guardian', 'player']
    def __str__(self):
        return f'{self.guardian.get_full_name()} - {self.player.get_full_name()} ({self.get_relation_display()})'