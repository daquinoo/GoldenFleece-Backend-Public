from django.urls import path
from .views import (
    prediction_detail,
    top_predictions,
    all_predictions,
    get_index_prices,       
    get_hot_stocks,        
    get_sector_performance,
    stock_detail,
    search_stocks,
)

urlpatterns = [
    path('prediction/<str:symbol>/', prediction_detail, name='prediction_detail'),
    path('top-predictions/', top_predictions, name='top_predictions'),
    path('all-predictions/', all_predictions, name='all_predictions'),

    
    path('index-prices/', get_index_prices, name='get_index_prices'),
    path('hot-stocks/', get_hot_stocks, name='get_hot_stocks'),
    path('sector-performance/', get_sector_performance, name='get_sector_performance'),
    path('stock/<str:symbol>/', stock_detail, name='stock_detail'),
    path('search-stocks/', search_stocks, name='search_stocks'),
]
