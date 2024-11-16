from django.urls import path
from .views import prediction_detail, top_predictions, all_predictions

urlpatterns = [
    path('prediction/<str:symbol>/', prediction_detail, name='prediction_detail'),
    path('top-predictions/', top_predictions, name='top_predictions'),
    path('all-predictions/', all_predictions, name='all_predictions'),
]
