from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

from users.models import GuardianProfile, AdminProfile
from players.models import Category, Player, GuardianPlayer
from finance.models import FeeDefinition, Invoice, Payment
from schedules.models import Match, Activity, Birthday
from communications.models import BulkEmail, EmailRecipient



class Command(BaseCommand):
    help = 'Seed the database with example data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        self.stdout.write('Starting data seeding...')
        
        # Create users and profiles
        self.create_users()
        
        # Create categories
        self.create_categories()
        
        # Create players
        self.create_players()
        
        # Create payments
        self.create_payments()
        
        # Create matches, activities and birthdays
        self.create_schedules()
        

        
        # Create communications
        self.create_communications()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with example data!')
        )

    def clear_data(self):
        """Clear existing data"""
        models_to_clear = [
            EmailRecipient, BulkEmail, Payment, Invoice, FeeDefinition, Birthday, Activity, Match,
            GuardianPlayer, Player, Category, GuardianProfile, AdminProfile
        ]
        
        for model in models_to_clear:
            model.objects.all().delete()
            
        # Clear users except superusers
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write('Data cleared successfully.')

    def create_users(self):
        """Create admin and guardian users"""
        self.stdout.write('Creating users...')
        
        # Create admin users
        admin_users = [
            {
                'username': 'admin_carlos',
                'email': 'carlos@deportespuertomontt.cl',
                'first_name': 'Carlos',
                'last_name': 'González',
                'phone': '+56912345678',
                'address': 'Av. Presidente Ibáñez 123, Puerto Montt'
            },
            {
                'username': 'admin_maria',
                'email': 'maria@deportespuertomontt.cl',
                'first_name': 'María',
                'last_name': 'Rodríguez',
                'phone': '+56987654321',
                'address': 'Calle Urmeneta 456, Puerto Montt'
            }
        ]
        
        for admin_data in admin_users:
            user = User.objects.create_user(
                username=admin_data['username'],
                email=admin_data['email'],
                password='admin123',
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name']
            )
            AdminProfile.objects.create(
                user=user,
                position='Administrador'
            )
        
        # Create guardian users
        guardian_users = [
            {
                'username': 'guardian_juan',
                'email': 'juan.perez@email.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'rut': '12345678-9',
                'phone': '+56912345001',
                'address': 'Los Aromos 789, Puerto Montt'
            },
            {
                'username': 'guardian_ana',
                'email': 'ana.martinez@email.com',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'rut': '23456789-0',
                'phone': '+56912345002',
                'address': 'Costanera 321, Puerto Montt'
            },
            {
                'username': 'guardian_pedro',
                'email': 'pedro.silva@email.com',
                'first_name': 'Pedro',
                'last_name': 'Silva',
                'rut': '34567890-1',
                'phone': '+56912345003',
                'address': 'Mirador 654, Puerto Montt'
            },
            {
                'username': 'guardian_lucia',
                'email': 'lucia.torres@email.com',
                'first_name': 'Lucía',
                'last_name': 'Torres',
                'rut': '45678901-2',
                'phone': '+56912345004',
                'address': 'Pelluco 987, Puerto Montt'
            },
            {
                'username': 'guardian_miguel',
                'email': 'miguel.herrera@email.com',
                'first_name': 'Miguel',
                'last_name': 'Herrera',
                'rut': '56789012-3',
                'phone': '+56912345005',
                'address': 'Alerce 147, Puerto Montt'
            }
        ]
        
        for guardian_data in guardian_users:
            user = User.objects.create_user(
                username=guardian_data['username'],
                email=guardian_data['email'],
                password='guardian123',
                first_name=guardian_data['first_name'],
                last_name=guardian_data['last_name']
            )
            GuardianProfile.objects.create(
                user=user,
                phone=guardian_data['phone'],
                address=guardian_data['address']
            )
        
        self.stdout.write(f'Created {len(admin_users)} admin users and {len(guardian_users)} guardian users.')

    def create_categories(self):
        """Create categories"""
        self.stdout.write('Creating categories...')
        
        # Create categories
        categories_data = [
            {'name': 'Sub-8'},
            {'name': 'Sub-10'},
            {'name': 'Sub-12'},
            {'name': 'Sub-14'},
            {'name': 'Sub-16'},
            {'name': 'Sub-18'}
        ]
        
        for category_data in categories_data:
            Category.objects.create(**category_data)
        
        self.stdout.write(f'Created {len(categories_data)} categories.')

    def create_players(self):
        """Create players and registrations"""
        self.stdout.write('Creating players...')
        
        guardians = User.objects.filter(guardian_profile__isnull=False)
        categories = Category.objects.all()
        
        players_data = [
            # Sub-10 Players
            {'first_name': 'Mateo', 'last_name': 'Pérez', 'birth_date': '2014-03-15', 'category': 'Sub-10'},
            {'first_name': 'Sofía', 'last_name': 'Martínez', 'birth_date': '2014-07-22', 'category': 'Sub-10'},
            {'first_name': 'Diego', 'last_name': 'Silva', 'birth_date': '2014-11-08', 'category': 'Sub-10'},
            {'first_name': 'Valentina', 'last_name': 'Torres', 'birth_date': '2014-05-30', 'category': 'Sub-10'},
            
            # Sub-12 Players
            {'first_name': 'Sebastián', 'last_name': 'Herrera', 'birth_date': '2012-04-12', 'category': 'Sub-12'},
            {'first_name': 'Isidora', 'last_name': 'González', 'birth_date': '2012-09-18', 'category': 'Sub-12'},
            {'first_name': 'Joaquín', 'last_name': 'Rodríguez', 'birth_date': '2012-12-03', 'category': 'Sub-12'},
            {'first_name': 'Emilia', 'last_name': 'López', 'birth_date': '2012-06-25', 'category': 'Sub-12'},
            
            # Sub-14 Players
            {'first_name': 'Benjamín', 'last_name': 'Morales', 'birth_date': '2010-02-14', 'category': 'Sub-14'},
            {'first_name': 'Antonia', 'last_name': 'Vega', 'birth_date': '2010-08-07', 'category': 'Sub-14'},
            {'first_name': 'Tomás', 'last_name': 'Castro', 'birth_date': '2010-10-19', 'category': 'Sub-14'},
            {'first_name': 'Florencia', 'last_name': 'Mendoza', 'birth_date': '2010-04-28', 'category': 'Sub-14'},
            
            # Sub-16 Players
            {'first_name': 'Maximiliano', 'last_name': 'Núñez', 'birth_date': '2008-01-20', 'category': 'Sub-16'},
            {'first_name': 'Catalina', 'last_name': 'Soto', 'birth_date': '2008-07-11', 'category': 'Sub-16'},
            {'first_name': 'Ignacio', 'last_name': 'Fernández', 'birth_date': '2008-11-02', 'category': 'Sub-16'},
            {'first_name': 'Javiera', 'last_name': 'Ruiz', 'birth_date': '2008-05-16', 'category': 'Sub-16'},
            
            # Sub-18 Players
            {'first_name': 'Cristóbal', 'last_name': 'Vargas', 'birth_date': '2006-03-09', 'category': 'Sub-18'},
            {'first_name': 'Constanza', 'last_name': 'Jiménez', 'birth_date': '2006-09-24', 'category': 'Sub-18'},
            {'first_name': 'Felipe', 'last_name': 'Ramírez', 'birth_date': '2006-12-15', 'category': 'Sub-18'},
            {'first_name': 'Maite', 'last_name': 'Espinoza', 'birth_date': '2006-06-08', 'category': 'Sub-18'}
        ]
        
        for i, player_data in enumerate(players_data):
            # Assign guardian cyclically
            guardian = guardians[i % len(guardians)]
            category = categories.get(name=player_data['category'])
            
            # Parse birth date
            birth_date = datetime.strptime(player_data['birth_date'], '%Y-%m-%d').date()
            
            player = Player.objects.create(
                first_name=player_data['first_name'],
                last_name=player_data['last_name'],
                birthdate=birth_date,
                category=category
            )
            
            # Create guardian-player relationship
            GuardianPlayer.objects.create(
                guardian=guardian,
                player=player,
                relation=random.choice(['padre', 'madre', 'tutor', 'abuelo', 'otro'])
            )
        
        self.stdout.write(f'Created {len(players_data)} players with guardian relationships.')

    def create_payments(self):
        """Create payment system"""
        self.stdout.write('Creating payment system...')
        
        # Create fee definitions
        categories = Category.objects.all()
        fee_definitions_data = [
            {'name': 'Cuota Mensual', 'amount': 25000, 'period': 'mensual'},
            {'name': 'Cuota Anual', 'amount': 280000, 'period': 'anual'},
            {'name': 'Inscripción', 'amount': 15000, 'period': 'anual'}
        ]
        
        for category in categories:
            for fee_data in fee_definitions_data:
                FeeDefinition.objects.create(
                    category=category,
                    name=f"{fee_data['name']} - {category.name}",
                    amount=fee_data['amount'],
                    period=fee_data['period']
                )
        
        # Create invoices and payments
        guardians = User.objects.filter(guardian_profile__isnull=False)
        players = Player.objects.all()
        fee_definitions = FeeDefinition.objects.all()
        
        for guardian in guardians:
            # Get players associated with this guardian
            guardian_players = players.filter(guardianplayer__guardian=guardian)
            
            for player in guardian_players:
                # Create 2-3 invoices per player
                num_invoices = random.randint(2, 3)
                for i in range(num_invoices):
                    due_date = timezone.now().date() - timedelta(days=random.randint(0, 90))
                    fee_def = random.choice(fee_definitions.filter(category=player.category))
                    
                    invoice = Invoice.objects.create(
                        guardian=guardian,
                        player=player,
                        fee_definition=fee_def,
                        amount=fee_def.amount,
                        due_date=due_date,
                        status=random.choice(['pendiente', 'pagada', 'atrasada'])
                    )
                    
                    # Create payment for some invoices
                    if invoice.status == 'pagada' or random.choice([True, False]):
                        Payment.objects.create(
                            invoice=invoice,
                            amount=invoice.amount,
                            paid_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                            method=random.choice(['efectivo', 'transferencia', 'tarjeta']),
                            status=random.choice(['completado', 'pendiente']),
                            transaction_id=f'TXN{random.randint(100000, 999999)}'
                        )
        
        self.stdout.write(f'Created fee definitions for all categories, and invoices/payments for all players.')



    def create_schedules(self):
        """Create matches, activities and birthdays"""
        self.stdout.write('Creating schedules...')
        
        categories = Category.objects.all()
        players = Player.objects.all()
        
        # Create matches
        opponents = [
            'Club Deportivo Osorno', 'Academia Puerto Varas', 'Escuela Frutillar FC',
            'Club Atlético Castro', 'Deportivo Ancud', 'Universidad de Los Lagos',
            'Club Social Llanquihue', 'Deportes Temuco Juvenil'
        ]
        
        for category in categories:
            # Create 3 matches for each category
            for i in range(3):
                match_date = timezone.now() + timedelta(days=random.randint(7, 60))
                
                Match.objects.create(
                    category=category,
                    title=f'Partido vs {random.choice(opponents)}',
                    opponent=random.choice(opponents),
                    starts_at=match_date,
                    location=random.choice([
                        'Estadio Municipal Puerto Montt',
                        'Cancha Club Deportivo',
                        'Complejo Deportivo Alerce',
                        'Estadio Visitante'
                    ])
                )
        
        # Create activities
        activity_types = ['entrenamiento', 'reunion', 'otro']
        activity_titles = [
            'Entrenamiento Técnico',
            'Entrenamiento Físico', 
            'Reunión de Apoderados',
            'Charla Técnica',
            'Evaluación Médica'
        ]
        
        for i in range(10):
            start_time = timezone.now() + timedelta(days=random.randint(1, 30), hours=random.randint(16, 19))
            end_time = start_time + timedelta(hours=random.randint(1, 3))
            
            Activity.objects.create(
                title=random.choice(activity_titles),
                type=random.choice(activity_types),
                starts_at=start_time,
                ends_at=end_time,
                location=random.choice([
                    'Cancha de Entrenamiento Principal',
                    'Sede del Club',
                    'Gimnasio Municipal',
                    'Sala de Reuniones'
                ]),
                description=f'Actividad programada para el club'
            )
        
        # Create birthdays for players
        from datetime import date
        for player in players:
            # Use the player's actual birthdate if available, otherwise create a random one
            if hasattr(player, 'birthdate') and player.birthdate:
                birthday_date = player.birthdate
            else:
                # Generate a random birthday
                birth_year = random.randint(2005, 2015)
                birth_month = random.randint(1, 12)
                birth_day = random.randint(1, 28)
                birthday_date = date(birth_year, birth_month, birth_day)
            
            Birthday.objects.create(
                player=player,
                date=birthday_date
            )
        
        self.stdout.write(f'Created matches, activities and birthdays.')





    def create_communications(self):
        """Create messages and notifications"""
        self.stdout.write('Creating communications...')
        
        admin_users = User.objects.filter(admin_profile__isnull=False)
        guardian_users = User.objects.filter(guardian_profile__isnull=False)
        
        # Create messages
        message_subjects = [
            'Información sobre próximo partido',
            'Cambio de horario de entrenamiento',
            'Recordatorio de pago mensual',
            'Invitación a reunión de apoderados',
            'Actualización de documentos requeridos',
            'Felicitaciones por el rendimiento',
            'Información sobre torneo de verano'
        ]
        
        message_contents = [
            'Estimado apoderado, le informamos que el próximo partido se realizará el sábado a las 10:00 AM.',
            'Por motivos de mantención de la cancha, el entrenamiento del miércoles se realizará a las 17:00 hrs.',
            'Recordamos que el pago de la mensualidad vence el día 5 de cada mes.',
            'Los invitamos a participar en la reunión de apoderados que se realizará el próximo viernes.',
            'Solicitamos actualizar los documentos de seguro médico de su pupilo.',
            'Felicitamos a su hijo/a por el excelente rendimiento mostrado en los últimos entrenamientos.',
            'Se aproxima nuestro torneo de verano. Más información en los próximos días.'
        ]
        
        for i in range(15):  # Create 15 messages
            sender = random.choice(admin_users)
            recipient = random.choice(guardian_users)
            subject = random.choice(message_subjects)
            content = random.choice(message_contents)
            
            # Create bulk email
            bulk_email = BulkEmail.objects.create(
                title=subject,
                body_html=f'<p>{content}</p>',
                created_by=sender
            )
            
            # Create email recipient
            EmailRecipient.objects.create(
                bulk_email=bulk_email,
                user=recipient,
                status=random.choice(['pendiente', 'enviado', 'fallido'])
            )
        
        # Create notifications
        notification_titles = [
            'Nuevo mensaje recibido',
            'Pago registrado exitosamente',
            'Próximo entrenamiento mañana',
            'Documento pendiente de entrega',
            'Partido cancelado por lluvia',
            'Felicitaciones por el triunfo',
            'Recordatorio: Reunión de apoderados'
        ]
        
        notification_messages = [
            'Tiene un nuevo mensaje del administrador del club.',
            'Su pago ha sido registrado correctamente en el sistema.',
            'Recordamos que mañana hay entrenamiento a las 16:00 hrs.',
            'Falta entregar el certificado médico actualizado.',
            'El partido de este sábado ha sido cancelado debido a las condiciones climáticas.',
            '¡Felicitaciones! Su equipo ganó el último partido 3-1.',
            'No olvide asistir a la reunión de apoderados este viernes.'
        ]
        
        for user in guardian_users:
            # Create 3-5 additional bulk emails per guardian
            for i in range(random.randint(3, 5)):
                title = random.choice(notification_titles)
                message = random.choice(notification_messages)
                
                # Create additional bulk email as notification
                bulk_email = BulkEmail.objects.create(
                    title=title,
                    body_html=f'<p>{message}</p>',
                    created_by=random.choice(admin_users)
                )
                
                # Create email recipient
                EmailRecipient.objects.create(
                    bulk_email=bulk_email,
                    user=user,
                    status=random.choice(['pendiente', 'enviado', 'fallido'])
                )
        
        self.stdout.write('Created messages and notifications for all users.')