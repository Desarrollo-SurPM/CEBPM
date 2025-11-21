from django import forms
from django.contrib.auth.models import User
from .models import GuardianProfile, AdminProfile, Registration
from players.models import Category # <-- Importación de Category (para los dos formularios)

# ===================================================================
# INICIO DEL FORMULARIO DE REGISTRO PÚBLICO (CORREGIDO)
# ===================================================================

class UserRegistrationForm(forms.ModelForm):
    """
    Formulario de solicitud de registro.
    Crea un Apoderado (User) inactivo y una Solicitud (Registration) pendiente.
    """
    
    # --- Campos para el Apoderado (User) ---
    first_name = forms.CharField(
        label='Nombre del Apoderado', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'})
    )
    last_name = forms.CharField(
        label='Apellido del Apoderado', 
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apellido'})
    )
    email = forms.EmailField(
        label='Email del Apoderado', 
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu.correo@ejemplo.com'})
    )
    password = forms.CharField(
        label='Crear Contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    # --- CAMPO CORREGIDO: 'guardian_phone' ---
    # Este campo es para el GuardianProfile, no para el Registration.
    # Lo definimos aquí para capturarlo y usarlo en el método .save()
    guardian_phone = forms.CharField(
        label='Teléfono del Apoderado (Contacto)',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'})
    )

    # --- Campo para la Categoría (del modelo Registration) ---
    team = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_registration_open=True),
        label='Categoría a la que postula',
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Selecciona una categoría disponible"
    )

    class Meta:
        model = Registration
        # --- CORREGIDO: 'guardian_phone' ELIMINADO DE ESTA LISTA ---
        fields = [
            'player_first_name', 'player_last_name', 'player_rut', 'player_birth_date',
            'team'
        ]
        labels = {
            'player_first_name': 'Nombre del Jugador(a)',
            'player_last_name': 'Apellido del Jugador(a)',
            'player_rut': 'RUT del Jugador(a) (Opcional)',
            'player_birth_date': 'Fecha de Nacimiento (Jugador/a)',
        }
        widgets = {
            'player_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'player_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'player_rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'player_birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            raise forms.ValidationError("Un apoderado con este email ya existe.")
        return email

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password_confirm
    
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        # Actualizar el queryset en caso de que las categorías cambien
        self.fields['team'].queryset = Category.objects.filter(is_registration_open=True)

    def save(self, commit=True):
        # 1. Crear el Apoderado (User) pero inactivo
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            is_active=False # El admin debe activarlo
        )
        
        # 2. Crear el Perfil de Apoderado
        # (Usa el 'guardian_phone' que capturamos)
        GuardianProfile.objects.create(
            user=user,
            phone=self.cleaned_data['guardian_phone']
        )
        
        # 3. Preparar la Solicitud (Registration)
        registration = super().save(commit=False)
        registration.guardian = user
        registration.team = self.cleaned_data['team'].name
        
        if commit:
            registration.save()
        return registration

class PlayerRegistrationForm(forms.ModelForm):
    """Formulario para que un apoderado logueado inscriba una nueva jugadora"""
    
    team = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_registration_open=True),
        label='Categoría',
        empty_label="Selecciona Categoría"
    )

    class Meta:
        model = Registration
        fields = [
            'player_first_name', 'player_last_name', 'player_rut', 
            'player_birth_date', 'team', 'emergency_contact', 
            'emergency_phone', 'medical_info'
        ]
        widgets = {
            'player_birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'player_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'player_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'player_rut': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

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

class CategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías en el admin panel"""
    class Meta:
        model = Category
        fields = ['name', 'is_registration_open']
        labels = {
            'name': 'Nombre de la Categoría (Ej: U15)',
            'is_registration_open': 'Permitir nuevas inscripciones públicas'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_registration_open': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }