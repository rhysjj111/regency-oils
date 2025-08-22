from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    # We can add new fields here later, e.g.:
    # phone_number = models.CharField(max_length=20, blank=True)
    # role = models.CharField(max_length=20, blank=True)
    pass

class Customer(models.Model):
    """Represents the business entity we have a contract with."""
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(unique=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

class Site(models.Model):
    """Represents a physical location for collection/delivery."""

    default_route = models.ForeignKey(
        'RouteDefinition', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        help_text="The route this site normally belongs to."
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sites')
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.customer.name} - {self.postcode}"

class Vehicle(models.Model):
    """A vehicle in the fleet."""
    registration_number = models.CharField(max_length=10, unique=True)
    nickname = models.CharField(max_length=50, help_text="e.g., 'Big Blue'")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nickname} ({self.registration_number})"

# NEW MODEL: To store the reusable route names.
class RouteDefinition(models.Model):
    """A template for a route, like 'Cardiff South' or 'Newport City'."""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True, help_text="Inactive routes won't be offered for new runs.")

    def __str__(self):
        return self.name

class Route(models.Model):
    """A planned collection/delivery run for a specific day, based on a RouteDefinition."""
    # UPDATED: Links to the new RouteDefinition model instead of a text field.
    definition = models.ForeignKey(RouteDefinition, on_delete=models.PROTECT)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    # This field handles the drivers by linking to the main User model.
    drivers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    route_date = models.DateField()

    class Meta:
        ordering = ['-route_date', 'definition']

    def __str__(self):
        return f"{self.definition.name} on {self.route_date}"

class Stop(models.Model):
    """An individual stop on a route."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    class FailureReason(models.TextChoices):
        NO_COLLECTION = 'NO_COLLECTION', 'Customer did not need a collection'
        SHOP_CLOSED = 'SHOP_CLOSED', 'Shop closed'
        POOR_ACCESS = 'POOR_ACCESS', 'Poor access'
        OTHER = 'OTHER', 'Other (see notes)'

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    site = models.ForeignKey(Site, on_delete=models.PROTECT)
    sequence = models.PositiveIntegerField(
        default=0,
        db_index=True
    )
    # A flag to highlight important stops.
    is_priority = models.BooleanField(default=False, help_text="Check this to highlight the stop for the driver.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.CharField(
        max_length=20, 
        choices=FailureReason.choices, 
        blank=True, 
        help_text="Reason for a failed stop"
    )
    invoice_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True, help_text="Driver notes for this stop")

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"Stop {self.sequence}: {self.site} on {self.route}"
    
    def get_inline_title(self):
        formatted_date = self.route.route_date.strftime("%d/%m/%Y")
        return f"{self.site.customer} - {formatted_date}"

class Collection(models.Model):
    """Records ALL transactions at a Stop."""
    class FreshOilContainer(models.TextChoices):
        BOX = 'BOX', 'Box (20L)'
        BARREL = 'BARREL', 'Barrel (200L)'

    stop = models.OneToOneField(Stop, on_delete=models.CASCADE, related_name='collection')

    waste_oil_quantity = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    payment_made = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    fresh_oil_container_type = models.CharField(max_length=10, choices=FreshOilContainer.choices, blank=True)
    fresh_oil_container_qty = models.PositiveIntegerField(default=0)
    fresh_oil_total_litres = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    payment_received = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    docket_number = models.CharField(max_length=50, blank=True)
    docket_image = models.ImageField(upload_to='dockets/%Y/%m/%d/', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction at {self.stop.site}"

class DailyVehicleLog(models.Model):
    """
    Records the start and end-of-day stock totals for a vehicle on a specific route.
    Filled out by the warehouse manager for auditing purposes.
    """
    route = models.OneToOneField(Route, on_delete=models.PROTECT, related_name="log")
    
    # Waste Oil tracking
    start_day_waste_oil = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    end_day_waste_oil = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # Fresh Oil tracking
    start_day_fresh_oil = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    end_day_fresh_oil = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    # Audit trail
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        help_text="Manager who verified the totals."
    )
    log_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.route}"

    @property
    def waste_oil_collected(self):
        """Calculates the net waste oil collected according to the log."""
        return self.end_day_waste_oil - self.start_day_waste_oil

    @property
    def fresh_oil_delivered(self):
        """Calculates the net fresh oil delivered according to the log."""
        return self.start_day_fresh_oil - self.end_day_fresh_oil