from django.urls import path
from .views import register_user
from django.http import JsonResponse
from .views import login_view, generate_qr, mark_attendance, todays_class, teacher_profile

def home(request):
    return JsonResponse({"message": "Welcome to AttenQR API"})

urlpatterns = [
    path('', home),
    path('login/', login_view, name='login'),
    path('register/', register_user, name='register'),
    path('generate-qr/', generate_qr, name='generate_qr'),
    path('mark-attendance/', mark_attendance, name='mark-attendance'),
    path('todays-class/', todays_class, name='todays-class'),
    path('teacher-profile/', teacher_profile, name='teacher-profile'),

]

    
