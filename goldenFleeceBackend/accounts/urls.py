from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_user, email_login

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', email_login, name='email_login'),  
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
