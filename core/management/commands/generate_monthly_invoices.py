from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import IntegrityError
# --- INICIO DE CORRECCIÓN ---
# Importamos los modelos desde sus apps correctas
from finance.models import FeeDefinition, Invoice
from players.models import Player, GuardianPlayer
# --- FIN DE CORRECCIÓN ---

class Command(BaseCommand):
    help = 'Genera las facturas (Invoices) mensuales para todas las jugadoras activas.'

    def handle(self, *args, **options):
        # 1. Definir el mes y año actual
        today = timezone.now().date()
        current_month = today.month
        current_year = today.year
        
        # Opcional: Definir una fecha de vencimiento estándar (ej. el día 10 del mes)
        try:
            due_date = today.replace(day=10)
        except ValueError:
            # Si hoy es día > 28 y el mes es febrero, etc.
            # Simplemente tomamos el último día del mes actual.
            next_month = today.replace(day=28) + timezone.timedelta(days=4)
            due_date = next_month - timezone.timedelta(days=next_month.day)

        self.stdout.write(self.style.NOTICE(f"Iniciando generación de cuotas para {current_month}/{current_year}..."))

        # 2. Obtener todas las definiciones de cuotas que son 'mensual'
        monthly_fees = FeeDefinition.objects.filter(period='mensual')
        
        if not monthly_fees.exists():
            self.stdout.write(self.style.WARNING("No hay definiciones de cuotas 'mensuales' configuradas. Saliendo."))
            return

        invoices_created_total = 0
        players_skipped_total = 0

        # 3. Iterar sobre cada tipo de cuota mensual (ej. "Mensualidad U15", "Mensualidad U17")
        for fee_def in monthly_fees:
            self.stdout.write(self.style.NOTICE(f"Procesando cuota: '{fee_def.name}'..."))
            
            # 4. Encontrar a todas las jugadoras que deben pagar esta cuota
            players_to_bill = Player.objects.filter(status='active')
            
            # Si la cuota es específica de una categoría (ej. "Mensualidad U15")
            if fee_def.category:
                players_to_bill = players_to_bill.filter(category=fee_def.category)
            
            if not players_to_bill.exists():
                self.stdout.write(f"  - No hay jugadoras activas en la categoría '{fee_def.category.name if fee_def.category else 'N/A'}' para esta cuota.")
                continue

            invoices_created_fee = 0
            players_skipped_fee = 0

            # 5. Iterar sobre las jugadoras y crear la factura si no existe
            for player in players_to_bill:
                
                # 6. (CLAVE) Verificar si ya existe una factura para este jugador, esta cuota Y este mes/año
                invoice_exists = Invoice.objects.filter(
                    player=player,
                    fee_definition=fee_def,
                    created_at__year=current_year, # Factura creada este año
                    created_at__month=current_month # Factura creada este mes
                ).exists()
                
                if not invoice_exists:
                    # 7. Encontrar al apoderado principal
                    guardian_link = GuardianPlayer.objects.filter(player=player).first()
                    
                    if guardian_link:
                        try:
                            Invoice.objects.create(
                                guardian=guardian_link.guardian,
                                player=player,
                                fee_definition=fee_def,
                                amount=fee_def.amount,
                                due_date=due_date,
                                status='pendiente'
                            )
                            invoices_created_fee += 1
                        except IntegrityError:
                            players_skipped_fee += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"  - OMITIDO (Jugadora sin apoderado): {player.get_full_name()}"))
                        players_skipped_fee += 1
                else:
                    players_skipped_fee += 1
            
            self.stdout.write(self.style.SUCCESS(f"  - Facturas creadas para '{fee_def.name}': {invoices_created_fee}"))
            self.stdout.write(f"  - Jugadoras omitidas (ya facturadas): {players_skipped_fee}")
            
            invoices_created_total += invoices_created_fee
            players_skipped_total += players_skipped_fee

        # --- Reporte Final ---
        self.stdout.write(self.style.SUCCESS("\n======================================="))
        self.stdout.write(self.style.SUCCESS("PROCESO DE FACTURACIÓN MENSUAL COMPLETADO"))
        self.stdout.write(f"  Total de facturas nuevas creadas: {invoices_created_total}")
        self.stdout.write(f"  Total de jugadoras omitidas: {players_skipped_total}")
        self.stdout.write(self.style.SUCCESS("======================================="))