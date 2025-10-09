from django import forms
from .models import Player

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'first_name', 'last_name', 'rut', 'birthdate', 'category', 
            'photo', 'position', 'status'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del jugador'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido del jugador'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'rut': 'RUT',
            'birthdate': 'Fecha de Nacimiento',
            'category': 'Categoría',
            'photo': 'Fotografía',
            'position': 'Posición en la cancha',
            'status': 'Estado',
        }