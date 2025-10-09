from datetime import timezone
from django.utils import timezone 
from django.db import models
from django.contrib.auth.models import User
from players.models import Category, Player
from sponsors.models import Sponsor # Importamos el modelo Sponsor
from decimal import Decimal


class FeeDefinition(models.Model):
    """Definición de cuotas"""
    PERIOD_CHOICES = [
        ('mensual', 'Mensual'),
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
        ('pagada', 'Pagada'),
        ('atrasada', 'Atrasada'),
    ]
    
    guardian = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Apoderado')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Jugador')
    fee_definition = models.ForeignKey(FeeDefinition, on_delete=models.CASCADE, verbose_name='Definición de cuota')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    due_date = models.DateField(verbose_name='Fecha de vencimiento')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado')
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
        # Auto-actualizar estado si está atrasada
        if self.is_overdue and self.status == 'pendiente':
            self.status = 'atrasada'
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Pagos realizados"""
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    ]
    
    METHOD_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('dummy', 'Pasarela Simulada'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, verbose_name='Factura')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    paid_at = models.DateTimeField(verbose_name='Fecha de pago')
    method = models.CharField(max_length=15, choices=METHOD_CHOICES, verbose_name='Método de pago')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pendiente', verbose_name='Estado')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='ID de transacción')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-paid_at']

    def __str__(self):
        return f'Pago {self.id} - ${self.amount} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        # Si el pago se completa, marcar la factura como pagada
        if self.status == 'completado' and self.invoice.status != 'pagada':
            self.invoice.status = 'pagada'
            self.invoice.save()
        super().save(*args, **kwargs)


# --- NUEVO MODELO ---
class Transaction(models.Model):
    """Registro de todas las transacciones financieras del club"""
    TRANSACTION_TYPE_CHOICES = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ]
    CATEGORY_CHOICES = [
        ('cuota_jugador', 'Cuota de Jugador'),
        ('aporte_auspiciador', 'Aporte de Auspiciador'),
        ('pago_proveedor', 'Pago a Proveedor'),
        ('venta_entradas', 'Venta de Entradas'),
        ('gasto_operativo', 'Gasto Operativo'),
        ('otro_ingreso', 'Otro Ingreso'),
        ('otro_egreso', 'Otro Egreso'),
    ]

    description = models.CharField(max_length=255, verbose_name='Descripción')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Tipo')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='Categoría')
    transaction_date = models.DateField(default=timezone.now, verbose_name='Fecha de Transacción')
    
    # Relaciones opcionales para mayor detalle
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Pago de Cuota Asociado')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Auspiciador Asociado')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
        ordering = ['-transaction_date']

    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.get_category_display()} - ${self.amount}'