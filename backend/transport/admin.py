from django.contrib import admin
from .models import (
    Vehicle, Driver, Route, RouteStop, TransportAssignment, TripLog,
    StudentTripAttendance, VehicleMaintenance, TransportPlan, 
    StudentTransportSubscription, DriverLogbook, VehicleServiceReminder
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['vehicle_number', 'registration_number', 'make', 'model', 'status', 'seating_capacity']
    list_filter = ['status', 'fuel_type', 'vehicle_type']
    search_fields = ['vehicle_number', 'registration_number', 'make', 'model']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'license_number', 'license_expiry', 'is_active']
    list_filter = ['is_active', 'license_expiry']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'license_number']
    raw_id_fields = ['user']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_number', 'route_name', 'vehicle', 'driver', 'total_distance_km', 'is_active']
    list_filter = ['is_active']
    search_fields = ['route_number', 'route_name']


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'stop_name', 'stop_order', 'pickup_time', 'dropoff_time']
    list_filter = ['route']
    search_fields = ['stop_name', 'address']


@admin.register(TransportPlan)
class TransportPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'route', 'monthly_fee', 'term_fee', 'is_active']
    list_filter = ['plan_type', 'is_active', 'route']
    search_fields = ['name', 'description']


@admin.register(StudentTransportSubscription)
class StudentTransportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['student', 'plan', 'pickup_stop', 'start_date', 'end_date', 'status']
    list_filter = ['status', 'plan', 'start_date']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    raw_id_fields = ['student']


@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    list_display = ['route', 'trip_date', 'driver', 'vehicle', 'trip_type', 'start_time', 'status']
    list_filter = ['trip_date', 'trip_type', 'status']
    date_hierarchy = 'trip_date'
    search_fields = ['route__route_number', 'driver__user__first_name', 'vehicle__vehicle_number']


@admin.register(DriverLogbook)
class DriverLogbookAdmin(admin.ModelAdmin):
    list_display = ['driver', 'vehicle', 'route', 'date', 'trip_type', 'distance_covered', 'students_count']
    list_filter = ['date', 'trip_type', 'driver']
    date_hierarchy = 'date'
    search_fields = ['driver__user__first_name', 'driver__user__last_name']


@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'maintenance_type', 'scheduled_date', 'status', 'cost']
    list_filter = ['status', 'maintenance_type', 'scheduled_date']
    search_fields = ['vehicle__vehicle_number', 'description']


@admin.register(VehicleServiceReminder)
class VehicleServiceReminderAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'reminder_type', 'due_date', 'is_sent']
    list_filter = ['reminder_type', 'is_sent', 'due_date']
    search_fields = ['vehicle__vehicle_number']


admin.site.register(TransportAssignment)
admin.site.register(StudentTripAttendance)
