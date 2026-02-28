from django.db import models
from online_shop.models import Product

# Create your models here.
class InventoryCategory(models.Model):
    name = models.CharField(null=False, blank=False, max_length=100)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    sku = models.CharField(max_length=20, unique=True)
    unit = models.CharField(max_length=20)
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity_reserved = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_points = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
class Ingredient(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    inventory = models.OneToOneField(Inventory, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.inventory.name} ({self.quantity} {self.unit})"
