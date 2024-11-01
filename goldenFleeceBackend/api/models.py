from django.db import models

class PredsDaily(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField(primary_key=True)
    pred = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    pred_sign = models.IntegerField(null=True, blank=True)
    actual = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    actual_sign = models.IntegerField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    pred_open = models.FloatField(null=True, blank=True)   
    pred_close = models.FloatField(null=True, blank=True)  
    actual_open = models.FloatField(null=True, blank=True) 
    actual_close = models.FloatField(null=True, blank=True)
    pred_open_sign = models.IntegerField(null=True, blank=True)
    pred_close_sign = models.IntegerField(null=True, blank=True)
    actual_open_sign = models.IntegerField(null=True, blank=True)
    actual_close_sign = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'PredsDaily'  # Table name in database
        managed = False
        unique_together = (('symbol', 'date'),)

    def __str__(self):
        return f"{self.symbol} - {self.date}"
