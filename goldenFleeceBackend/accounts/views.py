from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import Watchlist
from .serializers import UserSerializer, WatchlistSerializer

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def email_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    try:
        # Fetch the user by email
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Authenticate using the username linked to the email
    user = authenticate(username=user.username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })
    return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_watchlist(request):
    """
    Returns the authenticated user's watchlist.
    """
    user = request.user
    items = Watchlist.objects.filter(user=user).order_by('-created_at')
    serializer = WatchlistSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_watchlist(request):
    """
    Add a stock symbol to the user's watchlist.
    Expect JSON body: { "symbol": "AAPL" }
    """
    user = request.user
    symbol = request.data.get('symbol', '').upper()
    if not symbol:
        return Response({"error": "Symbol is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if it already exists in watchlist (optional)
    existing = Watchlist.objects.filter(user=user, symbol=symbol).first()
    if existing:
        return Response({"message": "Symbol already in watchlist"}, status=status.HTTP_200_OK)

    new_item = Watchlist.objects.create(user=user, symbol=symbol)
    serializer = WatchlistSerializer(new_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_watchlist(request):
    """
    Remove a stock symbol from the user's watchlist.
    Expect JSON body: { "symbol": "AAPL" }
    """
    user = request.user
    symbol = request.data.get('symbol', '').upper()
    if not symbol:
        return Response({"error": "Symbol is required"}, status=status.HTTP_400_BAD_REQUEST)

    watchlist_item = Watchlist.objects.filter(user=user, symbol=symbol).first()
    if not watchlist_item:
        return Response({"error": "Symbol not found in watchlist"}, status=status.HTTP_404_NOT_FOUND)

    watchlist_item.delete()
    return Response({"message": f"Removed {symbol} from watchlist"}, status=status.HTTP_200_OK)
