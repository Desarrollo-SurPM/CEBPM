from django import forms
from .models import FeeDefinition, Transaction, Category
from players.models import Category, Player

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'category', 'description', 'amount', 'date', 'player']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pago árbitros Final U15'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'player': forms.Select(attrs={'class': 'form-select'}),
        }

class AssignFeeForm(forms.Form):
    """
    Formulario para que el Admin asigne una cuota masivamente a una categoría.
    """
    fee_definition = forms.ModelChoiceField(
        queryset=FeeDefinition.objects.all(),
        label="Cuota a Asignar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Asignar a la Categoría",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    due_date = forms.DateField(
        label="Fecha de Vencimiento",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text="Fecha límite para que los apoderados paguen esta cuota."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Hacemos que la fecha de vencimiento por defecto sea en 30 días
        from django.utils import timezone
        from datetime import timedelta
        self.fields['due_date'].initial = timezone.now().date() + timedelta(days=30)

class FeeDefinitionForm(forms.ModelForm):
    # Hacemos que la categoría sea opcional
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label="Categoría (Opcional)",
        help_text="Si no se selecciona, se aplica a todas las categorías (ej. Matrícula General)."
    )

    class Meta:
        model = FeeDefinition
        fields = ['name', 'category', 'amount', 'period']
        labels = {
            'name': 'Nombre de la Cuota',
            'amount': 'Monto',
            'period': 'Período',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Mensualidad U15'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }