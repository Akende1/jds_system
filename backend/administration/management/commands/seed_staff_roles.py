"""
Seed staff roles with sample data for testing cooking, cleaning, and security staff workflows
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from administration.models import User, Staff, StaffRole
from finance.models import StockItem, StudentLunchSubscription, LunchPlan
from finance.models import AcademicYear
from administration.models import Student


class Command(BaseCommand):
    help = 'Seed StaffRole data and create sample stock items for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding staff roles and stock items...'))
        
        # Get the Auxiliary staff member if it exists
        auxiliary_user = User.objects.filter(username='Auxilery').first()
        if not auxiliary_user or not hasattr(auxiliary_user, 'staff_profile'):
            self.stdout.write(self.style.ERROR('Auxiliary staff user not found. Please create one first.'))
            return
        
        auxiliary_staff = auxiliary_user.staff_profile
        
        # Create Staff Roles
        roles_created = 0
        for role_choice, role_display in StaffRole.ROLE_CHOICES:
            role, created = StaffRole.objects.get_or_create(
                staff=auxiliary_staff,
                role_type=role_choice,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'  ✓ Created role: {role_display}')
                roles_created += 1
            else:
                self.stdout.write(f'  ℹ️ Role already exists: {role_display}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Processed {StaffRole.ROLE_CHOICES.__len__()} staff roles'))
        
        # Create Sample Stock Items
        stock_items = [
            {'name': 'Maize Meal', 'category': 'Grains', 'unit': 'bags', 'quantity': 5, 'unit_cost': 500.00, 'min_threshold': 2},
            {'name': 'Cooking Oil', 'category': 'Cooking Essentials', 'unit': 'liters', 'quantity': 10, 'unit_cost': 150.00, 'min_threshold': 3},
            {'name': 'Sugar', 'category': 'Sweeteners', 'unit': 'kg', 'quantity': 8, 'unit_cost': 80.00, 'min_threshold': 2},
            {'name': 'Salt', 'category': 'Seasonings', 'unit': 'kg', 'quantity': 5, 'unit_cost': 30.00, 'min_threshold': 1},
            {'name': 'Tomatoes', 'category': 'Vegetables', 'unit': 'boxes', 'quantity': 0, 'unit_cost': 200.00, 'min_threshold': 2},
            {'name': 'Eggs', 'category': 'Proteins', 'unit': 'dozen', 'quantity': 3, 'unit_cost': 400.00, 'min_threshold': 2},
            {'name': 'Rice', 'category': 'Grains', 'unit': 'bags', 'quantity': 4, 'unit_cost': 600.00, 'min_threshold': 1},
            {'name': 'Beans', 'category': 'Legumes', 'unit': 'bags', 'quantity': 3, 'unit_cost': 400.00, 'min_threshold': 1},
        ]
        
        items_created = 0
        for item_data in stock_items:
            item, created = StockItem.objects.get_or_create(
                name=item_data['name'],
                defaults={
                    'category': item_data['category'],
                    'unit': item_data['unit'],
                    'current_quantity': item_data['quantity'],
                    'unit_cost': item_data['unit_cost'],
                    'minimum_threshold': item_data['min_threshold'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created stock item: {item_data["name"]} ({item_data["quantity"]} {item_data["unit"]})')
                items_created += 1
            else:
                self.stdout.write(f'  ℹ️ Stock item already exists: {item_data["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created/verified {items_created} stock items'))
        
        # Create a sample lunch plan and subscription for testing
        try:
            current_year = AcademicYear.objects.filter(is_current=True).first()
            if not current_year:
                # Create one if it doesn't exist
                current_year = AcademicYear.objects.create(
                    name='2025/2026',
                    start_date=timezone.now().date(),
                    end_date=timezone.now().date() + timezone.timedelta(days=365),
                    is_current=True
                )
                self.stdout.write(f'  ✓ Created current academic year: {current_year.name}')
            
            lunch_plan, created = LunchPlan.objects.get_or_create(
                name='Full Month Lunch Plan',
                defaults={
                    'plan_type': 'full_month',
                    'monthly_fee': 2000.00,
                    'description': 'Students get lunch every school day',
                    'is_active': True,
                    'academic_year': current_year,
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created lunch plan: {lunch_plan.name}')
            
            # Subscribe some students to lunch plan
            students = Student.objects.filter(status='active')[:3]
            subs_created = 0
            for student in students:
                sub, created = StudentLunchSubscription.objects.get_or_create(
                    student=student,
                    plan=lunch_plan,
                    defaults={
                        'start_date': timezone.now().date(),
                        'status': 'active',
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Subscribed {student.user.get_full_name()} to lunch plan')
                    subs_created += 1
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created {subs_created} lunch subscriptions for testing'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Could not create lunch subscriptions: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Seeding complete! Staff is now configured for:'))
        self.stdout.write('   • Cooking staff (can request restocking)')
        self.stdout.write('   • Cleaning staff (has access to cleaning portal)')
        self.stdout.write('   • Security staff (has access to security portal)')
        self.stdout.write(f'   • {items_created} stock items for kitchen operations')
