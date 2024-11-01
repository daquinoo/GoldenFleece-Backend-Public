from rest_framework import serializers
from .models import PredsDaily

class PredsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = PredsDaily
        fields = '__all__'
