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
    inUpper = models.BooleanField(null=True, blank=True) 
    inLower = models.BooleanField(null=True, blank=True) 
    Above = models.BooleanField(null=True, blank=True)    
    Below = models.BooleanField(null=True, blank=True)    
    Perfect = models.BooleanField(null=True, blank=True)  
    inUpperO = models.BooleanField(null=True, blank=True) 
    inLowerO = models.BooleanField(null=True, blank=True) 
    PerfectO = models.BooleanField(null=True, blank=True)  
    inUpperC = models.BooleanField(null=True, blank=True) 
    inLowerC = models.BooleanField(null=True, blank=True) 
    PerfectC = models.BooleanField(null=True, blank=True)  
    AboveO = models.BooleanField(null=True, blank=True)    
    BelowO = models.BooleanField(null=True, blank=True)    
    AboveC = models.BooleanField(null=True, blank=True)    
    BelowC = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'PredsDaily'  # Table name in database
        managed = False
        unique_together = (('symbol', 'date'),)

    def __str__(self):
        return f"{self.symbol} - {self.date}"

class PredsWeekly(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField(primary_key=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    pred_open = models.FloatField(null=True, blank=True)
    pred_close = models.FloatField(null=True, blank=True)
    pred_open_sign = models.IntegerField(null=True, blank=True)
    pred_close_sign = models.IntegerField(null=True, blank=True)
    actual_open = models.FloatField(null=True, blank=True)
    actual_close = models.FloatField(null=True, blank=True)
    actual_open_sign = models.IntegerField(null=True, blank=True)
    actual_close_sign = models.IntegerField(null=True, blank=True) 

    class Meta:
        db_table = 'PredsWeekly'  
        managed = False
        unique_together = (('symbol', 'date'),)

    def __str__(self):
        return f"{self.symbol} - {self.date}"

class PredsMonthly(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField(primary_key=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    pred_open = models.FloatField(null=True, blank=True)
    pred_close = models.FloatField(null=True, blank=True)
    pred_open_sign = models.IntegerField(null=True, blank=True)
    pred_close_sign = models.IntegerField(null=True, blank=True)
    actual_open = models.FloatField(null=True, blank=True)
    actual_close = models.FloatField(null=True, blank=True)
    actual_open_sign = models.IntegerField(null=True, blank=True)
    actual_close_sign = models.IntegerField(null=True, blank=True) 

    class Meta:
        db_table = 'PredsMonthly'  
        managed = False
        unique_together = (('symbol', 'date'),)

    def __str__(self):
        return f"{self.symbol} - {self.date}"



class DailyAcc(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    backAcc = models.FloatField(null=True, blank=True)
    liveAcc = models.FloatField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    MktCap = models.FloatField(null=True, blank=True)
    upper_95 = models.FloatField(null=True, blank=True)
    lower_95 = models.FloatField(null=True, blank=True)
    upper_95O = models.FloatField(null=True, blank=True)
    lower_95O = models.FloatField(null=True, blank=True)
    upper_95C = models.FloatField(null=True, blank=True)
    lower_95C = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'DailyAcc'
        managed = False

    def __str__(self):
        return self.symbol


class WeeklyAcc(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    backAcc = models.FloatField(null=True, blank=True)
    liveAcc = models.FloatField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    MktCap = models.FloatField(null=True, blank=True)
    upper_95 = models.FloatField(null=True, blank=True)
    lower_95 = models.FloatField(null=True, blank=True)
    upper_95O = models.FloatField(null=True, blank=True)
    lower_95O = models.FloatField(null=True, blank=True)
    upper_95C = models.FloatField(null=True, blank=True)
    lower_95C = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = 'WeeklyAcc'
        managed = False


class MonthlyAcc(models.Model):
    symbol = models.CharField(max_length=10, primary_key=True)
    backAcc = models.FloatField(null=True, blank=True)
    liveAcc = models.FloatField(null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    MktCap = models.FloatField(null=True, blank=True)
    upper_95 = models.FloatField(null=True, blank=True)
    lower_95 = models.FloatField(null=True, blank=True)
    upper_95O = models.FloatField(null=True, blank=True)
    lower_95O = models.FloatField(null=True, blank=True)
    upper_95C = models.FloatField(null=True, blank=True)
    lower_95C = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = 'MonthlyAcc'
        managed = False