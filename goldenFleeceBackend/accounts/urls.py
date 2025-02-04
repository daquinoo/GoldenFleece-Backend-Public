from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_user,
    email_login,
    get_watchlist,
    add_to_watchlist,
    remove_from_watchlist  
)

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', email_login, name='email_login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('watchlist/', get_watchlist, name='get_watchlist'),
    path('watchlist/add/', add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/', remove_from_watchlist, name='remove_from_watchlist'),  # <--
]
