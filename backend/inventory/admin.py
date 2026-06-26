from django.contrib import admin
from .models import ItemCategory, InventoryItem, StockTransaction, AssetAssignment, MaintenanceSchedule, MaintenanceRecord


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_code', 'category', 'quantity', 'unit_price', 'reorder_level']
    list_filter = ['category']
    search_fields = ['name', 'item_code']


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'transaction_type', 'quantity', 'transaction_date', 'issued_by']
    list_filter = ['transaction_type', 'transaction_date']
    search_fields = ['item__name', 'reference_number']
    raw_id_fields = ['issued_by']


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ['item', 'assigned_to', 'assigned_date', 'expected_return_date', 'actual_return_date', 'status']
    list_filter = ['status', 'assigned_date']
    search_fields = ['item__name', 'assigned_to__first_name']
    raw_id_fields = ['assigned_to']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['item', 'maintenance_type', 'next_maintenance_date', 'frequency', 'is_active']
    list_filter = ['is_active', 'maintenance_type', 'frequency']
    search_fields = ['item__name', 'description']


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['item', 'maintenance_date', 'performed_by', 'cost', 'status']
    list_filter = ['status', 'maintenance_date']
    search_fields = ['item__name', 'work_description', 'performed_by']
