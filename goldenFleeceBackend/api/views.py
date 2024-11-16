from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PredsDaily
from .serializers import PredsDailySerializer
from django.db.models import Max, F, FloatField, ExpressionWrapper

# View for getting symbol prediction
@api_view(['GET'])
def prediction_detail(request, symbol):
    try:
        # Get the latest date for the symbol
        latest_date = PredsDaily.objects.filter(symbol__iexact=symbol).aggregate(Max('date'))['date__max']
        # Get the prediction for that date
        prediction = PredsDaily.objects.get(symbol__iexact=symbol, date=latest_date)
        serializer = PredsDailySerializer(prediction)
        return Response(serializer.data)
    except PredsDaily.DoesNotExist:
        return Response({'error': 'Prediction not found'}, status=404)

# View for getting top predictions
# Gets top 20 predictions
@api_view(['GET'])
def top_predictions(request, count=20):
    try:
        # Get the latest date
        latest_date = PredsDaily.objects.aggregate(Max('date'))['date__max']
        # Filter predictions for that date
        predictions = PredsDaily.objects.filter(date=latest_date)

        # Annotate with predicted change percentage
        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )
        # Order by predicted change descending and limit to count
        top_stocks = predictions.order_by('-predicted_change_percentage')[:count]
        serializer = PredsDailySerializer(top_stocks, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching top predictions'}, status=500)

# View for getting all predictions
@api_view(['GET'])
def all_predictions(request):
    try:
        # Get the latest date
        latest_date = PredsDaily.objects.aggregate(Max('date'))['date__max']
        # Filter predictions for that date
        predictions = PredsDaily.objects.filter(date=latest_date)

        # Annotate with predicted change percentage
        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )

        # Optionally, you can order the predictions
        predictions = predictions.order_by('symbol')  # Or any other field

        serializer = PredsDailySerializer(predictions, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching all predictions'}, status=500)