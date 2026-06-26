from django.db import models
from django.utils import timezone
from administration.models import User, Student


class Vehicle(models.Model):
    """School transport vehicles"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
        ('retired', 'Retired'),
    )
    
    vehicle_number = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    
    vehicle_type = models.CharField(max_length=50, help_text="e.g., Bus, Van, Car")
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    
    seating_capacity = models.IntegerField()
    fuel_type = models.CharField(max_length=50, 
                                 choices=(('petrol', 'Petrol'), ('diesel', 'Diesel'), 
                                        ('electric', 'Electric'), ('hybrid', 'Hybrid')))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    purchase_date = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField()
    road_tax_expiry = models.DateField(null=True, blank=True)
    fitness_certificate_expiry = models.DateField(null=True, blank=True)
    
    current_mileage = models.IntegerField(default=0)
    
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vehicle_number']
        
    def __str__(self):
        return f"{self.vehicle_number} - {self.make} {self.model}"


class Driver(models.Model):
    """Transport drivers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    
    license_number = models.CharField(max_length=50, unique=True)
    license_type = models.CharField(max_length=50)
    license_expiry = models.DateField()
    
    experience_years = models.IntegerField(default=0)
    
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(max_length=17)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['employee_id']
        
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"


class Route(models.Model):
    """Transport routes"""
    route_number = models.CharField(max_length=50, unique=True)
    route_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    
    total_distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_duration_minutes = models.IntegerField()
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='routes')
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='routes')
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['route_number']
        
    def __str__(self):
        return f"{self.route_number} - {self.route_name}"


class RouteStop(models.Model):
    """Stops along a route"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=200)
    address = models.TextField()
    
    stop_order = models.IntegerField()
    
    pickup_time = models.TimeField(help_text="Morning pickup time")
    dropoff_time = models.TimeField(help_text="Afternoon drop-off time")
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['route', 'stop_order']
        unique_together = ['route', 'stop_order']
        
    def __str__(self):
        return f"{self.route.route_number} - Stop {self.stop_order}: {self.stop_name}"


class TransportAssignment(models.Model):
    """Assign students to transport routes"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transport_assignments')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='student_assignments')
    pickup_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name='pickup_students')
    dropoff_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name='dropoff_students',
                                    null=True, blank=True)
    
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['route', 'student']
        
    def __str__(self):
        return f"{self.student.full_name} - {self.route.route_name}"


class TripLog(models.Model):
    """Daily trip logs"""
    TRIP_TYPE_CHOICES = (
        ('pickup', 'Morning Pickup'),
        ('dropoff', 'Afternoon Drop-off'),
        ('special', 'Special Trip'),
    )
    
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trip_logs')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trip_logs')
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='trip_logs')
    
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES)
    trip_date = models.DateField(default=timezone.now)
    
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    start_mileage = models.IntegerField(null=True, blank=True)
    end_mileage = models.IntegerField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    students_count = models.IntegerField(default=0)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-trip_date', '-start_time']
        
    def __str__(self):
        return f"{self.route.route_number} - {self.trip_date} ({self.get_trip_type_display()})"


class StudentTripAttendance(models.Model):
    """Track which students were on each trip"""
    STATUS_CHOICES = (
        ('boarded', 'Boarded'),
        ('absent', 'Absent'),
        ('left_at_stop', 'Left at Stop'),
    )
    
    trip = models.ForeignKey(TripLog, on_delete=models.CASCADE, related_name='student_attendance')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='trip_attendance')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='boarded')
    pickup_time = models.TimeField(null=True, blank=True)
    dropoff_time = models.TimeField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['trip', 'student']
        ordering = ['trip', 'student']
        verbose_name_plural = 'Student Trip Attendances'
        
    def __str__(self):
        return f"{self.student.full_name} - {self.trip}"


class VehicleMaintenance(models.Model):
    """Vehicle maintenance records"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    
    maintenance_type = models.CharField(max_length=100)
    description = models.TextField()
    
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    service_provider = models.CharField(max_length=200)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    mileage_at_service = models.IntegerField(null=True, blank=True)
    next_service_due_km = models.IntegerField(null=True, blank=True)
    next_service_due_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        verbose_name_plural = 'Vehicle Maintenance Records'
        
    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.maintenance_type} ({self.scheduled_date})"


class TransportPlan(models.Model):
    """Monthly transport service plans"""
    PLAN_TYPE_CHOICES = (
        ('pickup_only', 'Pickup Only'),
        ('dropoff_only', 'Drop-off Only'),
        ('both_ways', 'Both Ways'),
    )
    
    name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='transport_plans')
    
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    term_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.route.route_name} - K{self.monthly_fee}/month"


class StudentTransportSubscription(models.Model):
    """Student enrollment in transport service"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='transport_subscriptions')
    plan = models.ForeignKey(TransportPlan, on_delete=models.PROTECT)
    pickup_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name='subscription_pickups')
    dropoff_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name='subscription_dropoffs',
                                    null=True, blank=True)
    
    guardian_contact = models.CharField(max_length=17, help_text="Guardian phone for pickup/dropoff")
    alternate_contact = models.CharField(max_length=17, blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    pause_start = models.DateField(null=True, blank=True)
    pause_end = models.DateField(null=True, blank=True)
    pause_reason = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.plan.name}"


class DriverLogbook(models.Model):
    """Daily driver logbook entries"""
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='logbook_entries')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='logbook_entries')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='logbook_entries')
    
    date = models.DateField()
    trip_type = models.CharField(max_length=20, choices=(
        ('morning_pickup', 'Morning Pickup'),
        ('afternoon_dropoff', 'Afternoon Drop-off'),
    ))
    
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    start_mileage = models.IntegerField()
    end_mileage = models.IntegerField()
    distance_covered = models.IntegerField(help_text="Auto-calculated")
    
    fuel_used = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    students_count = models.IntegerField(default=0)
    
    incidents = models.TextField(blank=True, help_text="Any incidents during the trip")
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.distance_covered = self.end_mileage - self.start_mileage
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-date', '-start_time']
        
    def __str__(self):
        return f"{self.driver.user.get_full_name()} - {self.date} ({self.get_trip_type_display()})"


class VehicleServiceReminder(models.Model):
    """Automated service reminders for vehicles"""
    REMINDER_TYPE_CHOICES = (
        ('insurance', 'Insurance Renewal'),
        ('road_tax', 'Road Tax'),
        ('fitness', 'Fitness Certificate'),
        ('service', 'Regular Service'),
        ('inspection', 'Inspection'),
    )
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='service_reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPE_CHOICES)
    
    due_date = models.DateField()
    reminder_date = models.DateField(help_text="Date to send reminder")
    
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['due_date']
        
    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.get_reminder_type_display()} due {self.due_date}"

