from django import forms
from .models import Ticket, TicketReply

class TicketForm(forms.ModelForm):
    """
    Formulario para que el apoderado cree un nuevo ticket.
    El primer mensaje se guarda en el modelo TicketReply.
    """
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        label="Escribe tu consulta"
    )

    class Meta:
        model = Ticket
        fields = ['subject', 'message']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Duda sobre pago de cuota'}),
        }
        labels = {
            'subject': 'Asunto de la Solicitud',
        }

class ReplyForm(forms.ModelForm):
    """
    Formulario para añadir una respuesta (admin o apoderado).
    """
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Escribe tu respuesta...'}),
        }
        labels = {
            'message': '', # Ocultamos la etiqueta para un look de chat
        }