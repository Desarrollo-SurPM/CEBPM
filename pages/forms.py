from django import forms
from .models import LandingNews, LandingEvent

class LandingNewsForm(forms.ModelForm):
    class Meta:
        model = LandingNews
        fields = ['image', 'tag', 'title', 'content', 'created_at']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: PLAYOFF'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'created_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        labels = {
            'image': 'Imagen de la Noticia',
            'tag': 'Etiqueta',
            'title': 'Título',
            'content': 'Párrafo',
            'created_at': 'Fecha de Publicación (para "hace X días")',
        }

class LandingEventForm(forms.ModelForm):
    class Meta:
        model = LandingEvent
        fields = ['title', 'date', 'event_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Partido vs Rival X'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'title': 'Título del Evento',
            'date': 'Fecha y Hora',
            'event_type': 'Tipo de Evento',
        }