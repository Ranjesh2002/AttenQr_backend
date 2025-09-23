from django.urls import path
from .views import register_user
from django.http import JsonResponse
from .views import login_view, admin_login, generate_qr, mark_attendance, todays_class, teacher_profile, student_profile, attendance_history, student_atten, student_attendance, Alerts, student_atten_percentage, streak, low_attendance_list, send_alerts, create_class_session, get_all_teachers, list_class_sessions, delete_class_session, total_teacher, total_stu, total_departments, update_teacher, average_attendance_percentage, attendance_list, student_detail, student_atten_admin, admin_attendance_history, today_attendance_history, attendance_by_session, average_attendance_today, weekly_attendance_trend, subject_wise_attendance, parent_login, parent_dashboard_view
from rest_framework_simplejwt.views import  TokenRefreshView

def home(request):
    return JsonResponse({"message": "Welcome to AttenQR API"})

urlpatterns = [
    path('', home),
    path('login/', login_view, name='login'),
    path('admin-login/', admin_login, name='admin-login'),
    path('parent-login/', parent_login, name='parent-login'),
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
    path('alerts/low-attendance/', low_attendance_list, name='low-attendance'),
    path('alerts/send-alerts/', send_alerts, name='send-alerts'),
    path('create-class-session/', create_class_session, name='create-class-session'),
    path('teachers/', get_all_teachers),
    path('class-sessions/', list_class_sessions),
    path('delete-class-session/<int:session_id>/', delete_class_session, name='delete-class-session'),
    path('total_teacher/', total_teacher, name='total_teacher'),
    path('total_stu/', total_stu, name='total_stu'),
    path('total_departments/', total_departments, name='total_departments'),
    path('update_teacher/<int:teacher_id>/', update_teacher, name='update_teacher'),
    path('average_percentage/', average_attendance_percentage, name='average_attendance_percentage'),
    path('attendance_list/', attendance_list, name='attendance_list'),
    path('student_detail/<int:student_id>/', student_detail, name='student_detail'),
    path('student_atten_admin/<int:student_id>/', student_atten_admin, name='student_atten_admin'),
    path('admin_attendance_history/', admin_attendance_history, name='admin_attendance_history'),
    path('today_attendance_history/', today_attendance_history, name='today_attendance_history'),
    path('attendance_by_class_session/<int:class_session_id>/', attendance_by_session, name='attendance_by_class_session'),
    path('average_attendance_today/', average_attendance_today, name='average_attendance_today'),
    path('weekly_attendance_trend/', weekly_attendance_trend, name='weekly_attendance_trend'),
    path('subject_wise_attendance/', subject_wise_attendance, name='subject_wise_attendance'),
    path('subject_wise_attendance/', subject_wise_attendance, name='subject_wise_attendance'),
    path('parent_dashboard_view/', parent_dashboard_view, name='parent_dashboard_view'),


]


    
