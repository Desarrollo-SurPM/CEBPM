from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import GuardianProfile, AdminProfile
from .forms import CustomUserCreationForm


def register_view(request):
    """Vista para registro de nuevos usuarios (apoderados)"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada exitosamente para {username}! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    """Vista del perfil del usuario"""
    user = request.user
    context = {'user': user}
    
    # Verificar si es admin o guardian
    try:
        admin_profile = AdminProfile.objects.get(user=user)
        context['profile'] = admin_profile
        context['user_type'] = 'admin'
    except AdminProfile.DoesNotExist:
        try:
            guardian_profile = GuardianProfile.objects.get(user=user)
            context['profile'] = guardian_profile
            context['user_type'] = 'guardian'
        except GuardianProfile.DoesNotExist:
            context['profile'] = None
            context['user_type'] = 'unknown'
    
    return render(request, 'users/profile.html', context)


def home_redirect(request):
    """Redirige a los usuarios según su tipo después del login"""
    if request.user.is_authenticated:
        # Si es superuser, redirigir al admin de Django
        if request.user.is_superuser:
            return redirect('/admin/')
        
        # Verificar si es admin
        try:
            AdminProfile.objects.get(user=request.user)
            return redirect('/admin-panel/')
        except AdminProfile.DoesNotExist:
            pass
        
        # Verificar si es guardian
        try:
            GuardianProfile.objects.get(user=request.user)
            return redirect('/guardian/')
        except GuardianProfile.DoesNotExist:
            pass
        
        # Por defecto, redirigir al perfil
        return redirect('profile')
    
    # Si no está autenticado, redirigir a la landing page
    return redirect('pages:landing')
