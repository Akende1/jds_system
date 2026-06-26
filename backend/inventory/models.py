from django.db import models
from django.utils import timezone
from administration.models import User


class ItemCategory(models.Model):
    """Categories for inventory items"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Item Categories'
        
    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Items in the school inventory"""
    CONDITION_CHOICES = (
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    )
    
    item_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, related_name='items')
    
    description = models.TextField()
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    reorder_level = models.IntegerField(default=10, help_text="Minimum quantity before reordering")
    
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='new')
    location = models.CharField(max_length=200, help_text="Where the item is stored")
    
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    
    supplier_name = models.CharField(max_length=200, blank=True)
    supplier_contact = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    image = models.ImageField(upload_to='inventory/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Inventory Items'
        
    def __str__(self):
        return f"{self.item_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total value
        self.total_value = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    @property
    def needs_reorder(self):
        return self.quantity <= self.reorder_level


class StockTransaction(models.Model):
    """Track stock movements (in/out)"""
    TRANSACTION_TYPE_CHOICES = (
        ('purchase', 'Purchase'),
        ('issue', 'Issue/Dispatch'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('damage', 'Damage/Loss'),
        ('donation', 'Donation'),
    )
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    quantity = models.IntegerField()
    transaction_date = models.DateTimeField(default=timezone.now)
    
    issued_to = models.CharField(max_length=200, blank=True, help_text="Person/Department receiving the item")
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_issues')
    
    reference_number = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-transaction_date']
        
    def __str__(self):
        return f"{self.item.name} - {self.get_transaction_type_display()} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update inventory quantity based on transaction type
            if self.transaction_type in ['purchase', 'return', 'donation']:
                self.item.quantity += self.quantity
            elif self.transaction_type in ['issue', 'damage']:
                self.item.quantity -= self.quantity
            self.item.save()


class AssetAssignment(models.Model):
    """Track assignment of assets to staff/students"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    )
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_assets')
    
    assigned_date = models.DateField(default=timezone.now)
    expected_return_date = models.DateField(null=True, blank=True)
    actual_return_date = models.DateField(null=True, blank=True)
    
    condition_at_issue = models.CharField(max_length=10, choices=InventoryItem.CONDITION_CHOICES)
    condition_at_return = models.CharField(max_length=10, choices=InventoryItem.CONDITION_CHOICES, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-assigned_date']
        
    def __str__(self):
        return f"{self.item.name} assigned to {self.assigned_to.get_full_name()}"


class MaintenanceSchedule(models.Model):
    """Maintenance schedule for assets"""
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    )
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='maintenance_schedules')
    maintenance_type = models.CharField(max_length=100)
    description = models.TextField()
    
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField()
    
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['next_maintenance_date']
        
    def __str__(self):
        return f"{self.item.name} - {self.maintenance_type}"


class MaintenanceRecord(models.Model):
    """Record of maintenance performed"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='records')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='maintenance_records')
    
    maintenance_date = models.DateField(default=timezone.now)
    performed_by = models.CharField(max_length=200)
    
    work_description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    parts_replaced = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    
    next_maintenance_due = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-maintenance_date']
        
    def __str__(self):
        return f"{self.item.name} - Maintenance on {self.maintenance_date}"

