from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL

class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    coin_id = models.CharField(max_length=100)
    coin_name = models.CharField(max_length=255)
    coin_symbol = models.CharField(max_length=20)
    coin_image = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("user","coin_id")
        ordering = ["-created_at"]

class PortfolioHolding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="holdings")
    coin_id = models.CharField(max_length=100)
    coin_name = models.CharField(max_length=255)
    coin_symbol = models.CharField(max_length=20)
    coin_image = models.URLField()
    amount = models.DecimalField(max_digits=20, decimal_places=10)
    purchase_price_usd = models.DecimalField(max_digits=20, decimal_places=2)
    purchase_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]

class PriceAlert(models.Model):
    CONDITION_CHOICES = [("above","Above"),("below","Below")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    coin_id = models.CharField(max_length=100)
    coin_name = models.CharField(max_length=255)
    coin_symbol = models.CharField(max_length=20)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    target_price_usd = models.DecimalField(max_digits=20, decimal_places=2)
    is_active = models.BooleanField(default=True)
    triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
