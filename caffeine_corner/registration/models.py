"""Registration app models.

Contains the UserProfile model and related business logic for roles and PII fields.
"""

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class UserProfile(models.Model):
    """Profile data associated one-to-one with a user.

    Stores role, phone number, and address (PII). Be mindful of data exposure in admin/views.
    """

    class Roles(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF = "staff", "Staff"
        CUSTOMER = "customer", "Customer"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        # ForeignKeys are indexed by default in Django, explicit index optional
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
        db_index=True,
        help_text="The user's role within the system.",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                # Consider using django-phonenumber-field for robust validation
                regex=r"^\+?[0-9()\-\s]{7,20}$",
                message="Enter a valid phone number.",
            )
        ],
        db_index=True,
        help_text="Optional contact number (PII)",
    )
    address = models.TextField(blank=True, help_text="Postal address (PII)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Cross-table ordering is convenient but can be slower on large datasets
        ordering = ("user__username",)
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"
        # Example conditional unique constraint if phone must be unique when present:
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["phone_number"],
        #         condition=~models.Q(phone_number=""),
        #         name="uniq_userprofile_phone_non_empty",
        #     ),
        # ]

    def __str__(self) -> str:
        # Django users implement get_username
        return self.user.get_username()

    def clean(self) -> None:
        # Chain to base validations
        super().clean()
        # Normalize fields
        if self.phone_number:
            # Collapse spaces and trim
            self.phone_number = " ".join(self.phone_number.split()).strip()
        if self.address:
            # Collapse multiple whitespace to single spaces
            self.address = " ".join(self.address.split())
