from django.db import models

class CoinPriceCache(models.Model):
    coin_id = models.CharField(max_length=100, unique=True)
    price_usd = models.DecimalField(max_digits=20, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
