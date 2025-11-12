from django import forms
from .models import Player, PlayerDocument


class PlayerForm(forms.ModelForm):
    """
    Formulario COMPLETO para que el Administrador edite la ficha.
    """
    class Meta:
        model = Player
        # Incluimos todos los campos que el admin debe gestionar
        fields = [
            'first_name', 'last_name', 'nickname', 'rut', 'birthdate', 'photo', 
            'player_email', 'player_phone', 'category', 'position', 'status', 
            'height', 'association', 'medical_conditions', 'permissions_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'player_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'player_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Estatura en cm (ej: 170.5)'}),
            'association': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Federación de Básquetbol de Chile'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Alergias, condiciones pre-existentes, etc.'}),
            'permissions_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Permiso de imagen, autorizaciones de viaje, etc.'}),
        }

class PlayerGuardianEditForm(forms.ModelForm):
    """
    Formulario LIMITADO para que el Apoderado edite solo datos
    personales y médicos.
    """
    class Meta:
        model = Player
        # El apoderado solo puede editar estos campos:
        fields = [
            'photo', 'player_email', 'player_phone', 
            'medical_conditions', 'permissions_notes'
        ]
        labels = {
            'photo': 'Actualizar Foto de la Jugadora',
            'player_email': 'Email de Contacto de la Jugadora',
            'player_phone': 'Teléfono de Contacto de la Jugadora',
            'medical_conditions': 'Condiciones Médicas y Alergias',
            'permissions_notes': 'Permisos y Autorizaciones (Ej: Uso de imagen)'
        }
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'player_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'player_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Alergias conocidas, condiciones pre-existentes, etc.'}),
            'permissions_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ej: "Autorizo el uso de imagen para redes sociales del club".'}),
        }

class PlayerDocumentForm(forms.ModelForm):
    """
    Formulario para subir un nuevo documento para una jugadora.
    """
    class Meta:
        model = PlayerDocument
        fields = ['title', 'file']
        labels = {
            'title': 'Título del Documento',
            'file': 'Seleccionar Archivo (PDF, JPG, PNG)',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Permiso de Imagen 2025'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }