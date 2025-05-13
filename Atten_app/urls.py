from django.urls import path
from .views import register_user
from django.http import JsonResponse
from .views import LoginAPIView

def home(request):
    return JsonResponse({"message": "Welcome to AttenQR API"})

urlpatterns = [
    path('', home),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('register/', register_user, name='register'),
]

