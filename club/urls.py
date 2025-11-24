# club/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    
    # Apps principales
    path('pages/', include('pages.urls')),
    path('auth/', include('users.urls')),
    path('admin-panel/', include('users.admin_urls')),
    path('guardian/', include('users.guardian_urls')),
    
    # --- AÑADIR ESTA LÍNEA ---
    path('tickets/', include('tickets.urls', namespace='tickets')),
    # Nuevas URLs funcionales
    path('finance/', include('finance.urls')),
    path('schedules/', include('schedules.urls')),
    path('players/', include('players.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
