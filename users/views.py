from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User # <-- Importación añadida

# --- FORMULARIO DE REGISTRO CORRECTO ---
from .forms import UserRegistrationForm

# --- IMPORTACIONES DE MODELOS CORREGIDAS ---
# Player NO está en .models, está en players.models
from .models import GuardianProfile, AdminProfile 
from players.models import Player # <-- Esta es la importación correcta

# ==============================================
# VISTA home_redirect (fusionada y corregida)
# ==============================================
def home_redirect(request):
    """Redirige a los usuarios según su tipo después del login"""
    if request.user.is_authenticated:
        # Si es superuser, redirigir al admin de Django
        if request.user.is_superuser:
            return redirect('/admin/')
        
        # Verificar si es admin
        try:
            AdminProfile.objects.get(user=request.user)
            # Usamos el nombre de la URL con namespace
            return redirect('admin_panel:dashboard')
        except AdminProfile.DoesNotExist:
            pass
        
        # Verificar si es guardian
        try:
            GuardianProfile.objects.get(user=request.user)
            # Usamos el nombre de la URL con namespace
            return redirect('guardian:dashboard')
        except GuardianProfile.DoesNotExist:
            pass
        
        # Si es un usuario logueado pero sin perfil (raro), va a la landing
        return redirect('pages:landing')
    
    # Si no está autenticado, redirigir a la landing page
    return redirect('pages:landing')

# ==============================================
# VISTA DE REGISTRO (la nueva que crea la solicitud)
# ==============================================
def register_view(request):
    """Vista de registro público para Apoderados y su primera Jugadora."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # El método .save() del formulario ahora crea el User (inactivo),
            # el GuardianProfile y la Solicitud de Registration.
            form.save()
            
            messages.success(request, '¡Solicitud enviada! Un administrador revisará tu registro. Serás notificado por correo cuando tu cuenta sea aprobada.')
            return redirect('pages:landing')
        else:
            messages.error(request, 'Hubo un error en el formulario. Por favor, revisa los campos.')
    else:
        form = UserRegistrationForm()
        
    # Verificar si hay categorías abiertas
    if not form.fields['team'].queryset.exists():
         messages.warning(request, 'Actualmente no hay inscripciones abiertas para ninguna categoría.')

    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)

# ==============================================
# VISTA DE PERFIL (la que yo había borrado)
# ==============================================
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

# ==============================================
# VISTAS DE LOGIN Y LOGOUT (sin cambios)
# ==============================================
def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return home_redirect(request)
        
    if request.method == 'POST':
        form = request.POST
        username = form.get('username')
        password = form.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenido de vuelta, {user.first_name}!')
                return home_redirect(request)
            else:
                messages.error(request, 'Esta cuenta está inactiva. Contacta al administrador.')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            
    return render(request, 'registration/login.html')


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Has cerrado sesión exitosamente.')
        return redirect('pages:landing')
    
    # Si se accede por GET, redirigir
    return redirect('pages:landing')