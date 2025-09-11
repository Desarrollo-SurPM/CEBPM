from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GuardianProfile, AdminProfile


class CustomUserCreationForm(UserCreationForm):
    """Formulario personalizado para registro de usuarios"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nombre'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu apellido'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56 9 1234 5678'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Dirección completa'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            if field_name in ['username', 'password1', 'password2']:
                field.widget.attrs['class'] = 'form-control'
            
            # Placeholders personalizados
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Nombre de usuario'
            elif field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Contraseña'
            elif field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Confirmar contraseña'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Crear perfil de apoderado
            GuardianProfile.objects.create(
                user=user,
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', '')
            )
        return user


class GuardianProfileForm(forms.ModelForm):
    """Formulario para editar perfil de apoderado"""
    
    class Meta:
        model = GuardianProfile
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa'
            })
        }


class AdminProfileForm(forms.ModelForm):
    """Formulario para editar perfil de administrador"""
    
    class Meta:
        model = AdminProfile
        fields = ['position']
        widgets = {
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Director Técnico, Presidente, etc.'
            })
        }


class UserUpdateForm(forms.ModelForm):
    """Formulario para actualizar información básica del usuario"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            })
        }
