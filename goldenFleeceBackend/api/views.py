from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PredsDaily, PredsWeekly, PredsMonthly, DailyAcc, WeeklyAcc, MonthlyAcc
from .serializers import PredsDailySerializer, PredsWeeklySerializer, PredsMonthlySerializer, DailyAccSerializer, WeeklyAccSerializer, MonthlyAccSerializer
from django.db.models import Max, F, FloatField, ExpressionWrapper

# View for getting symbol prediction
@api_view(['GET'])
def prediction_detail(request, symbol):
    try:
        time_frame = request.GET.get('timeFrame', 'daily').lower()

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
            AccModel = DailyAcc
            AccSerializer = DailyAccSerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
            AccModel = WeeklyAcc
            AccSerializer = WeeklyAccSerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
            AccModel = MonthlyAcc
            AccSerializer = MonthlyAccSerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.filter(symbol__iexact=symbol).aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'Prediction not found'}, status=404)

        prediction = PredictionModel.objects.get(symbol__iexact=symbol, date=latest_date)
        prediction_serializer = PredictionSerializer(prediction)

        # Get confidence intervals
        acc_data = AccModel.objects.get(symbol__iexact=symbol)
        acc_serializer = AccSerializer(acc_data)

        # Combine data
        data = prediction_serializer.data
        data.update(acc_serializer.data)

        return Response(data)
    except PredictionModel.DoesNotExist:
        return Response({'error': 'Prediction not found'}, status=404)
    except AccModel.DoesNotExist:
        return Response({'error': 'Confidence interval data not found'}, status=404)
    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred'}, status=500)
    


# View for getting top predictions
@api_view(['GET'])
def top_predictions(request):
    try:

        time_frame = request.GET.get('timeFrame', 'daily').lower()
        count = int(request.GET.get('count', 20))

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'No predictions available'}, status=404)

        predictions = PredictionModel.objects.filter(date=latest_date)

        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )

        top_stocks = predictions.order_by('-predicted_change_percentage')[:count]
        serializer = PredictionSerializer(top_stocks, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching top predictions'}, status=500)

# View for getting all predictions
@api_view(['GET'])
def all_predictions(request):
    try:
        time_frame = request.GET.get('timeFrame', 'daily').lower()

        if time_frame == 'daily':
            PredictionModel = PredsDaily
            PredictionSerializer = PredsDailySerializer
        elif time_frame == 'weekly':
            PredictionModel = PredsWeekly
            PredictionSerializer = PredsWeeklySerializer
        elif time_frame == 'monthly':
            PredictionModel = PredsMonthly
            PredictionSerializer = PredsMonthlySerializer
        else:
            return Response({'error': 'Invalid time frame'}, status=400)

        latest_date = PredictionModel.objects.aggregate(Max('date'))['date__max']
        if not latest_date:
            return Response({'error': 'No predictions available'}, status=404)

        predictions = PredictionModel.objects.filter(date=latest_date)

        predictions = predictions.annotate(
            predicted_change_percentage=ExpressionWrapper(
                F('pred_close') * 100,
                output_field=FloatField()
            )
        )
        # Currently ordering by symbol
        predictions = predictions.order_by('symbol')

        serializer = PredictionSerializer(predictions, many=True)
        return Response(serializer.data)
    except Exception as e:
        print(e)
        return Response({'error': 'Error fetching all predictions'}, status=500)