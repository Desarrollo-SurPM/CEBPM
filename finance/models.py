from django.db import models
from django.contrib.auth.models import User
from players.models import Category, Player
from decimal import Decimal
from sponsors.models import Sponsor


class FeeDefinition(models.Model):
    """Definición de cuotas"""
    PERIOD_CHOICES = [
        ('mensual', 'Mensual'),
        ('unico', 'Pago Único'),
        ('anual', 'Anual'),
    ]
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Categoría')
    name = models.CharField(max_length=100, verbose_name='Nombre')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, verbose_name='Período')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Definición de Cuota'
        verbose_name_plural = 'Definiciones de Cuotas'
        ordering = ['name']

    def __str__(self):
        category_name = self.category.name if self.category else 'General'
        return f'{self.name} - {category_name} (${self.amount})'


class Invoice(models.Model):
    """Facturas de cuotas"""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('atrasada', 'Atrasada'),
        ('en revisión', 'En Revisión'),  # <-- NUEVO ESTADO
        ('pagada', 'Pagada'),
    ]
    
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Apoderado')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Jugador')
    fee_definition = models.ForeignKey(FeeDefinition, on_delete=models.CASCADE, verbose_name='Definición de cuota')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    due_date = models.DateField(verbose_name='Fecha de vencimiento')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado') # Ajustado max_length
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-due_date']

    def __str__(self):
        player_name = f' - {self.player.get_full_name()}' if self.player else ''
        return f'Factura {self.id} - {self.guardian.get_full_name()}{player_name}'

    @property
    def is_overdue(self):
        from datetime import date
        return self.due_date < date.today() and self.status == 'pendiente'

    def save(self, *args, **kwargs):
        # Auto-actualizar estado si está atrasada (pero no si está en revisión o pagada)
        if self.is_overdue and self.status == 'pendiente':
            self.status = 'atrasada'
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Pagos realizados"""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente de Aprobación'), # <-- CAMBIADO
        ('completado', 'Completado'),
        ('fallido', 'Rechazado'), # <-- CAMBIADO
    ]
    
    # AJUSTADO para coincidir con tu plantilla pay_quota.html
    METHOD_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('efectivo', 'Efectivo'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('cheque', 'Cheque'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name='Factura')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    paid_at = models.DateTimeField(verbose_name='Fecha de pago') # El apoderado la define al subir el pago
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='Método de pago') # Ajustado max_length
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado')
    
    # --- NUEVOS CAMPOS ---
    payment_proof = models.ImageField(
        upload_to='payment_proofs/', 
        null=True, 
        blank=False, # Requerido para este flujo
        verbose_name='Comprobante de Pago'
    )
    notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='Notas (Nro. Transacción)'
    )
    # --- FIN NUEVOS CAMPOS ---

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-paid_at']

    def __str__(self):
        return f'Pago {self.id} - ${self.amount} ({self.get_status_display()})'

class Transaction(models.Model):
    """
    Modelo para registrar transacciones financieras generales
    (Ingresos por sponsors, Gastos en árbitros, etc.)
    """
    TYPE_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('gasto', 'Gasto'),
    ]
    
    CATEGORY_CHOICES = [
        # Ingresos
        ('sponsor', 'Auspiciador'),
        ('evento', 'Evento'),
        ('donacion', 'Donación'),
        ('entrada', 'Entradas'),
        ('cuota', 'Cuota Social/Deportiva'), # Agregué esta por si acaso
        # Gastos
        ('arriendo', 'Arriendo Gimnasio'),
        ('arbitraje', 'Pago Árbitros'),
        ('proveedor', 'Pago Proveedores'),
        ('cuerpo_tecnico', 'Cuerpo Técnico'),
        ('equipamiento', 'Equipamiento'),
        ('transporte', 'Transporte'),
        ('otros', 'Otros'),
    ]

    # --- NUEVO: Tipo de aporte (Dinero o Especies) ---
    CONTRIBUTION_CHOICES = [
        ('monetary', 'Monetario (Dinero)'),
        ('goods', 'Implementos / Especies / Servicios'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipo')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Categoría')
    description = models.CharField(max_length=255, verbose_name='Descripción')
    amount = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='Monto Estimado/Real') # Cambié decimales a 0 si usas pesos chilenos, si usas USD déjalo en 2
    date = models.DateField(verbose_name='Fecha de Transacción')
    
    # --- NUEVO: Vínculo con Auspiciador ---
    sponsor = models.ForeignKey(
        Sponsor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Auspiciador (Si aplica)',
        related_name='transactions'
    )

    # --- NUEVO: Definir si es dinero o especies ---
    contribution_type = models.CharField(
        max_length=10, 
        choices=CONTRIBUTION_CHOICES, 
        default='monetary',
        verbose_name='Tipo de Aporte'
    )

    # Opcional: Para vincular un pago a un jugador específico
    player = models.ForeignKey(
        Player, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name='Jugador (Opcional)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-date']

    def __str__(self):
        prefix = ""
        if self.sponsor:
            prefix = f"[Sponsor: {self.sponsor.name}] "
        return f"{prefix}[{self.get_type_display()}] {self.description} - ${self.amount}"