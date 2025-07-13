from django.urls import path
from .views import register_user
from django.http import JsonResponse
from .views import login_view, admin_login, generate_qr, mark_attendance, todays_class, teacher_profile, student_profile, attendance_history, student_atten, student_attendance, Alerts, student_atten_percentage, streak
from rest_framework_simplejwt.views import  TokenRefreshView

def home(request):
    return JsonResponse({"message": "Welcome to AttenQR API"})

urlpatterns = [
    path('', home),
    path('login/', login_view, name='login'),
    path('admin-login/', admin_login, name='admin-login'),
    path('register/', register_user, name='register'),
    path('generate-qr/', generate_qr, name='generate_qr'),
    path('mark-attendance/', mark_attendance, name='mark-attendance'),
    path('todays-class/', todays_class, name='todays-class'),
    path('teacher-profile/', teacher_profile, name='teacher-profile'),
    path('student-profile/', student_profile, name='student-profile'),
    path('attendance-history/', attendance_history, name='attendance-history'),
    path('student-atten/<int:session_id>/', student_atten, name='student-atten'),
    path('student-attendance/', student_attendance, name='student-attendance'),
    path('alerts/', Alerts, name='Alerts'),
    path('student-atten-percentage/', student_atten_percentage, name='student_atten_percentage'),
    path('streak/', streak, name='streak'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


]

    
