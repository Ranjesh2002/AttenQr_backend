from django.urls import path
from .views import register_user
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Welcome to AttenQR API"})

urlpatterns = [
    path('', home),
    path('register/', register_user, name='register'),
]
