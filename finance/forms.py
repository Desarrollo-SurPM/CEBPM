from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'description', 'amount', 'transaction_type', 'category', 
            'transaction_date', 'sponsor'
        ]
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pago de arbitraje, Aporte de Auspiciador X'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto en CLP'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sponsor': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'description': 'Descripción de la Transacción',
            'amount': 'Monto',
            'transaction_type': 'Tipo (Ingreso/Egreso)',
            'category': 'Categoría',
            'transaction_date': 'Fecha de la Transacción',
            'sponsor': 'Auspiciador Asociado (Opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que el campo 'sponsor' no sea obligatorio
        self.fields['sponsor'].required = False