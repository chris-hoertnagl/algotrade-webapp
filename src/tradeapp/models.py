from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# Create your models here.
class SingleActiveModel(models.Model):
    active = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.active:
            # select all other active items
            qs = type(self).objects.filter(active=True)
            # except self (if self already exists)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            # and deactivate them
            qs.update(active=False)

        super(SingleActiveModel, self).save(*args, **kwargs)


class Algorithm(SingleActiveModel):
    SYMBOLS = (('BTCEUR', 'BTCEUR'), ('ETHEUR', 'ETHEUR'))
    name = models.CharField(max_length=16, primary_key=True, default='BTCtrade')
    symbol = models.CharField(max_length=16, default="BTCEUR", choices=SYMBOLS)
    stop_loss = models.FloatField(default=0.98, validators=[MinValueValidator(0), MaxValueValidator(1)])
    take_profit = models.FloatField(default=1.005, validators=[MinValueValidator(1.002), MaxValueValidator(2)])
    trade_qty = models.FloatField(default=0.0003)
    performance = models.FloatField(default=0.0)

    class Meta:
        app_label = 'tradeapp'


class Order(models.Model):
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    time = models.DateTimeField()
    symbol = models.CharField(max_length=8, default="default")
    price = models.FloatField(default=0)
    quantity = models.FloatField(default=0)
    type = models.CharField(max_length=10, default="default")
    time_in_force = models.CharField(max_length=3, default="default")
    side = models.CharField(max_length=6, default='ERROR')
    status = models.CharField(max_length=15, default='default')

    class Meta:
        app_label = 'tradeapp'


class Fill(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    price = models.FloatField()
    quantity = models.FloatField()
    commission = models.FloatField()
    commission_asset = models.CharField(max_length=4)

    class Meta:
        app_label = 'tradeapp'
