from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Products
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    sku = models.CharField(max_length=20, unique=True)
    barcode = models.CharField(max_length=150, db_index=True)
    image = models.ImageField(upload_to="product_images/", blank=True, max_length=255)
    sort_order = models.IntegerField(default=0, db_index=True)
    is_available = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    is_seasonal = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name", "-created_at")
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["sort_order", "name"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["is_available", "is_featured", "is_seasonal"]),
        ]
    @property
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 1)
        return None
    def __str__(self):
        return f"{self.name} ({self.sku})"


class Variant(models.Model):
    SIZE_CHOICES = (
        ("small", "Small"),
        ("medium", "Medium"),
        ("large", "Large"),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    additional_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )
    sku = models.CharField(max_length=20, unique=True)
    barcode = models.CharField(max_length=150, db_index=True)

    class Meta:
        ordering = ("product", "size")
        verbose_name = "Variant"
        verbose_name_plural = "Variants"

    def __str__(self):
        return f"{self.product.name} - {self.size}"


class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "product"], name="unique_user_product_rating"),
        ]
        ordering = ("-created_at",)
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.username}"


class CartItem(models.Model):
    """Cart items for MySQL-safe uniqueness.

    MySQL does not natively support partial unique indexes before 8.0 with full capability. To avoid
    portability issues, we enforce a single uniqueness across (user, product, variant). For items
    without a variant, we store variant as NULL but enforce uniqueness at the app level.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(9999)])

    class Meta:
        # In MySQL, a simple unique_together is reliable. We keep (user, product, variant) unique.
        unique_together = (("user", "product", "variant"),)
        ordering = ("user", "product", "variant")
        verbose_name = "Cart item"
        verbose_name_plural = "Cart items"
        indexes = [
            models.Index(fields=["user", "product"]),
        ]

    def __str__(self):
        if self.variant:
            return f"{self.user.username} - {self.product.name} ({self.variant.size}) x {self.quantity}"
        return f"{self.user.username} - {self.product.name} x {self.quantity}"

    def clean(self):
        # Optional: enforce app-level uniqueness for (user, product) when variant is NULL
        if self.variant is None and self.user_id and self.product_id:
            existing = CartItem.objects.filter(user_id=self.user_id, product_id=self.product_id, variant__isnull=True)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError("A cart item for this product without a variant already exists for this user.")


class LoyaltyPoint(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="loyalty")
    points = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_updated",)
        verbose_name = "Loyalty point"
        verbose_name_plural = "Loyalty points"

    def __str__(self):
        return f"{self.user.username} - {self.points} points"
