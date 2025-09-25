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
from sponsors.models import Sponsor


class Command(BaseCommand):
    help = 'Seed the database with example basketball data'

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
        
        self.create_users()
        self.create_categories()
        self.create_players()
        self.create_payments()
        self.create_schedules()
        self.create_communications()
        self.create_sponsors()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with example basketball data!')
        )

    def clear_data(self):
        """Clear existing data"""
        models_to_clear = [
            EmailRecipient, BulkEmail, Payment, Invoice, FeeDefinition, Birthday, Activity, Match,
            GuardianPlayer, Player, Category, GuardianProfile, AdminProfile, Sponsor
        ]
        
        for model in models_to_clear:
            model.objects.all().delete()
            
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('Data cleared successfully.')

    def create_users(self):
        """Create admin and guardian users"""
        self.stdout.write('Creating users...')
        admin_users_data = [
            {'username': 'admin_carlos', 'email': 'carlos@ceb.cl', 'first_name': 'Carlos', 'last_name': 'González'},
            {'username': 'admin_maria', 'email': 'maria@ceb.cl', 'first_name': 'María', 'last_name': 'Rodríguez'}
        ]
        for data in admin_users_data:
            user, created = User.objects.get_or_create(username=data['username'], defaults=data)
            if created:
                user.set_password('admin123')
                user.save()
            AdminProfile.objects.get_or_create(user=user, defaults={'position': 'Administrador'})

        guardian_users_data = [
            {'username': 'guardian_juan', 'email': 'juan.perez@email.com', 'first_name': 'Juan', 'last_name': 'Pérez', 'phone': '+56912345001', 'address': 'Los Aromos 789, Puerto Montt'},
            {'username': 'guardian_ana', 'email': 'ana.martinez@email.com', 'first_name': 'Ana', 'last_name': 'Martínez', 'phone': '+56912345002', 'address': 'Costanera 321, Puerto Montt'},
            {'username': 'guardian_pedro', 'email': 'pedro.silva@email.com', 'first_name': 'Pedro', 'last_name': 'Silva', 'phone': '+56912345003', 'address': 'Mirador 654, Puerto Montt'}
        ]
        for data in guardian_users_data:
            user, created = User.objects.get_or_create(username=data['username'], defaults={'email': data['email'], 'first_name': data['first_name'], 'last_name': data['last_name']})
            if created:
                user.set_password('guardian123')
                user.save()
            GuardianProfile.objects.get_or_create(user=user, defaults={'phone': data['phone'], 'address': data['address']})
        
        self.stdout.write(f'Created/verified {len(admin_users_data)} admin users and {len(guardian_users_data)} guardian users.')


    def create_categories(self):
        """Create basketball categories"""
        self.stdout.write('Creating basketball categories...')
        categories_data = [
            {'name': 'U-13'}, {'name': 'U-15'}, {'name': 'U-17'}, {'name': 'U-19'}, {'name': 'Adulto'},
        ]
        for category_data in categories_data:
            Category.objects.get_or_create(**category_data)
        self.stdout.write(f'Created {len(categories_data)} categories.')

    def create_players(self):
        """Create players and registrations"""
        self.stdout.write('Creating players...')
        guardians = User.objects.filter(guardian_profile__isnull=False)
        if not guardians.exists():
            self.stdout.write(self.style.WARNING('No guardians found, skipping player creation.'))
            return
            
        categories = Category.objects.all()
        players_data = [
            {'first_name': 'Mateo', 'last_name': 'Pérez', 'birth_date': '2011-03-15', 'category': 'U-13', 'position': 'base'},
            {'first_name': 'Sofía', 'last_name': 'Martínez', 'birth_date': '2011-07-22', 'category': 'U-13', 'position': 'escolta'},
            {'first_name': 'Diego', 'last_name': 'Silva', 'birth_date': '2009-11-08', 'category': 'U-15', 'position': 'alero'},
            {'first_name': 'Valentina', 'last_name': 'González', 'birth_date': '2009-05-30', 'category': 'U-15', 'position': 'ala_pivot'},
            {'first_name': 'Sebastián', 'last_name': 'Herrera', 'birth_date': '2007-04-12', 'category': 'U-17', 'position': 'pivot'},
            {'first_name': 'Isidora', 'last_name': 'Rodríguez', 'birth_date': '2007-09-18', 'category': 'U-17', 'position': 'base'},
            {'first_name': 'Joaquín', 'last_name': 'López', 'birth_date': '2005-12-03', 'category': 'U-19', 'position': 'escolta'},
            {'first_name': 'Emilia', 'last_name': 'Morales', 'birth_date': '2005-06-25', 'category': 'U-19', 'position': 'alero'},
            {'first_name': 'Benjamín', 'last_name': 'Vega', 'birth_date': '2003-02-14', 'category': 'Adulto', 'position': 'ala_pivot'},
            {'first_name': 'Antonia', 'last_name': 'Castro', 'birth_date': '2003-08-07', 'category': 'Adulto', 'position': 'pivot'},
        ]
        
        for i, player_data in enumerate(players_data):
            guardian = guardians[i % len(guardians)]
            category = categories.get(name=player_data['category'])
            birth_date = datetime.strptime(player_data['birth_date'], '%Y-%m-%d').date()
            
            player, created = Player.objects.get_or_create(
                first_name=player_data['first_name'],
                last_name=player_data['last_name'],
                defaults={'birthdate': birth_date, 'category': category, 'position': player_data['position']}
            )
            
            if created:
                GuardianPlayer.objects.create(
                    guardian=guardian,
                    player=player,
                    relation=random.choice(['padre', 'madre', 'tutor'])
                )
        self.stdout.write(f'Created {len(players_data)} players.')

    def create_payments(self):
        self.stdout.write('Creating payment system...')
        categories = Category.objects.all()
        fee_definitions_data = [
            {'name': 'Cuota Mensual', 'amount': 30000, 'period': 'mensual'},
            {'name': 'Matrícula Anual', 'amount': 20000, 'period': 'anual'}
        ]
        for category in categories:
            for fee_data in fee_definitions_data:
                FeeDefinition.objects.get_or_create(
                    category=category,
                    name=f"{fee_data['name']} - {category.name}",
                    defaults={'amount': fee_data['amount'], 'period': fee_data['period']}
                )
        guardians = User.objects.filter(guardian_profile__isnull=False)
        for guardian in guardians:
            guardian_players = Player.objects.filter(guardianplayer__guardian=guardian)
            for player in guardian_players:
                fee_def = FeeDefinition.objects.filter(category=player.category, period='mensual').first()
                if fee_def:
                    invoice, created = Invoice.objects.get_or_create(
                        guardian=guardian,
                        player=player,
                        fee_definition=fee_def,
                        due_date=timezone.now().date() - timedelta(days=random.randint(-15, 45)),
                        defaults={'amount': fee_def.amount}
                    )
                    if invoice.due_date < timezone.now().date():
                        invoice.status = 'atrasada'
                    if random.choice([True, False]):
                        invoice.status = 'pagada'
                    invoice.save()
        self.stdout.write('Created fee definitions and sample invoices.')

    def create_schedules(self):
        self.stdout.write('Creating schedules...')
        categories = Category.objects.all()
        players = Player.objects.all()
        opponents = ['CD Valdivia', 'ABA Ancud', 'CEB Puerto Varas', 'Atlético Puerto Varas', 'CD Castro']
        
        for category in categories:
            for i in range(2):
                match_date = timezone.now() + timedelta(days=random.randint(7, 45), hours=random.randint(1, 5))
                Match.objects.get_or_create(
                    title=f'Partido Liga Saesa vs {random.choice(opponents)}',
                    category=category,
                    defaults={'opponent': random.choice(opponents), 'starts_at': match_date, 'location': 'Gimnasio Municipal'}
                )
        
        activity_titles = ['Entrenamiento Físico', 'Práctica de Tiros', 'Charla Técnica', 'Reunión de Apoderados']
        for i in range(5):
            start_time = timezone.now() + timedelta(days=random.randint(2, 20), hours=random.randint(18, 20))
            Activity.objects.get_or_create(
                title=random.choice(activity_titles),
                defaults={'type': 'entrenamiento', 'starts_at': start_time, 'ends_at': start_time + timedelta(hours=2), 'location': 'Gimnasio Club'}
            )
        
        for player in players:
            if player.birthdate:
                Birthday.objects.get_or_create(player=player, defaults={'date': player.birthdate})
        self.stdout.write('Created matches, activities and birthdays.')

    def create_communications(self):
        self.stdout.write('Creating communications...')
        admin_users = User.objects.filter(admin_profile__isnull=False)
        guardian_users = User.objects.filter(guardian_profile__isnull=False)
        if not admin_users.exists() or not guardian_users.exists():
            self.stdout.write(self.style.WARNING('No admins or guardians found, skipping communications.'))
            return

        message_subjects = ['Info Partido Fin de Semana', 'Cambio Horario Entrenamiento', 'Recordatorio Cuota', 'Reunión Apoderados']
        for i in range(5):
            sender = random.choice(admin_users)
            recipient = random.choice(guardian_users)
            subject = random.choice(message_subjects)
            bulk_email = BulkEmail.objects.create(title=subject, body_html=f'<p>Mensaje de prueba sobre: {subject.lower()}.</p>', created_by=sender)
            EmailRecipient.objects.create(bulk_email=bulk_email, user=recipient, status='enviado')
        self.stdout.write('Created sample communications.')

    def create_sponsors(self):
        self.stdout.write('Creating sponsors...')
        sponsors_data = [
            {'name': 'Constructora local', 'active': True},
            {'name': 'Clínica de Salud', 'active': True},
            {'name': 'Tienda de Deportes', 'active': True},
            {'name': 'Supermercado Regional', 'active': False},
        ]
        for data in sponsors_data:
            Sponsor.objects.get_or_create(**data)
        self.stdout.write(f'Created {len(sponsors_data)} sponsors.')