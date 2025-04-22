from rest_framework import serializers
from .models import PredsDaily, PredsWeekly, PredsMonthly, DailyAcc, WeeklyAcc, MonthlyAcc, MonthlyGrade

class PredsDailySerializer(serializers.ModelSerializer):
    current_price = serializers.FloatField(required=False)
    class Meta:
        model = PredsDaily
        fields = '__all__'

class PredsWeeklySerializer(serializers.ModelSerializer):
    current_price = serializers.FloatField(required=False)
    class Meta:
        model = PredsWeekly
        fields = '__all__'

class PredsMonthlySerializer(serializers.ModelSerializer):
    current_price = serializers.FloatField(required=False)
    class Meta:
        model = PredsMonthly
        fields = '__all__'


class DailyAccSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyAcc
        fields = ['upper_95C', 'lower_95C']

class WeeklyAccSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyAcc
        fields = ['upper_95C', 'lower_95C']

class MonthlyAccSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyAcc
        fields = ['upper_95C', 'lower_95C']

class MonthlyGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyGrade
        fields = ['open_grade_sign', 'open_grade_class']