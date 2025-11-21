from django import forms
from .models import Sponsor

class SponsorForm(forms.ModelForm):
    class Meta:
        model = Sponsor
        fields = ['name', 'logo', 'website', 'contact_name', 'contact_phone', 'contact_email', 'is_visible']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://sitio-web.com'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona de contacto'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input ml-2'}),
        }
        labels = {
            'is_visible': '¿Visible en el sitio web?',
            'website': 'Sitio Web',
            'logo': 'Logo (Imagen)'
        }