from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Sponsor
from django import forms

# Formulario simple inline (o podrías ponerlo en forms.py)
class SponsorForm(forms.ModelForm):
    class Meta:
        model = Sponsor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'admin_profile')

@login_required
@user_passes_test(is_admin)
def sponsor_list(request):
    """Listar y Crear Auspiciadores"""
    if request.method == 'POST':
        form = SponsorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Auspiciador creado correctamente.')
            return redirect('sponsors:list')
    else:
        form = SponsorForm()
    
    sponsors = Sponsor.objects.all()
    return render(request, 'admin/sponsors.html', {'sponsors': sponsors, 'form': form})

@login_required
@user_passes_test(is_admin)
def sponsor_delete(request, pk):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    sponsor.delete()
    messages.success(request, 'Auspiciador eliminado.')
    return redirect('sponsors:list')