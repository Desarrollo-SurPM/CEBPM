from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import GuardianProfile, AdminProfile


class Command(BaseCommand):
    help = 'Borra todos los usuarios existentes y crea usuarios admin y apoderado específicos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando proceso de reseteo de usuarios...')
        
        # Borrar todos los usuarios existentes (excepto superusuarios)
        self.stdout.write('Borrando usuarios existentes...')
        
        # Primero borrar los perfiles relacionados
        GuardianProfile.objects.all().delete()
        AdminProfile.objects.all().delete()
        
        # Luego borrar todos los usuarios (excepto superusuarios)
        deleted_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(f'Se borraron {deleted_count} usuarios existentes.')
        
        # Crear usuario administrador
        self.stdout.write('Creando usuario administrador...')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ceb.cl',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'is_staff': True
            }
        )
        
        if created:
            admin_user.set_password('admin')
            admin_user.save()
            self.stdout.write(f'Usuario administrador creado: {admin_user.username}')
        else:
            # Actualizar contraseña si ya existe
            admin_user.set_password('admin')
            admin_user.is_staff = True
            admin_user.save()
            self.stdout.write(f'Usuario administrador actualizado: {admin_user.username}')
        
        # Crear perfil de administrador
        admin_profile, created = AdminProfile.objects.get_or_create(
            user=admin_user,
            defaults={'position': 'Administrador Principal'}
        )
        
        # Crear usuario apoderado
        self.stdout.write('Creando usuario apoderado...')
        guardian_user, created = User.objects.get_or_create(
            username='apoderado',
            defaults={
                'email': 'apoderado@ceb.cl',
                'first_name': 'Apoderado',
                'last_name': 'Ejemplo'
            }
        )
        
        if created:
            guardian_user.set_password('apoderado')
            guardian_user.save()
            self.stdout.write(f'Usuario apoderado creado: {guardian_user.username}')
        else:
            # Actualizar contraseña si ya existe
            guardian_user.set_password('apoderado')
            guardian_user.save()
            self.stdout.write(f'Usuario apoderado actualizado: {guardian_user.username}')
        
        # Crear perfil de apoderado
        guardian_profile, created = GuardianProfile.objects.get_or_create(
            user=guardian_user,
            defaults={
                'phone': '+56 9 1234 5678',
                'address': 'Dirección de ejemplo, Puerto Montt'
            }
        )
        
        # Crear usuario admin de deportes
        self.stdout.write('Creando usuario admin de deportes...')
        sports_admin_user, created = User.objects.get_or_create(
            username='admin1',
            defaults={
                'email': 'admin1@ceb.cl',
                'first_name': 'Admin',
                'last_name': 'Deportes',
                'is_staff': True
            }
        )
        
        if created:
            sports_admin_user.set_password('admin1')
            sports_admin_user.save()
            self.stdout.write(f'Usuario admin de deportes creado: {sports_admin_user.username}')
        else:
            # Actualizar contraseña si ya existe
            sports_admin_user.set_password('admin1')
            sports_admin_user.is_staff = True
            sports_admin_user.save()
            self.stdout.write(f'Usuario admin de deportes actualizado: {sports_admin_user.username}')
        
        # Crear perfil de administrador para admin de deportes
        sports_admin_profile, created = AdminProfile.objects.get_or_create(
            user=sports_admin_user,
            defaults={'position': 'Administrador de Deportes'}
        )
        
        self.stdout.write(
            self.style.SUCCESS('¡Proceso completado exitosamente!')
        )
        self.stdout.write('Usuarios creados:')
        self.stdout.write(f'  - Admin: usuario="admin", contraseña="admin"')
        self.stdout.write(f'  - Admin Deportes: usuario="admin1", contraseña="admin1"')
        self.stdout.write(f'  - Apoderado: usuario="apoderado", contraseña="apoderado"')