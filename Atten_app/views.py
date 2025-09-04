from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student, Teacher, QRCodeSession, Attendance, ClassSession,StudentAlert
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from datetime import timedelta, date
import os
from jinja2 import Template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .serializers import AdminLoginSerializer, ClassSessionSerializer
from .services import admin_login_service, get_class_sessions

@api_view(['POST'])
def register_user(request):
    data = request.data

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    student_id = data.get('studentId')
    department = data.get('department')
    year = data.get('year')

    if not all([name, email, password, role]):
        return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'error': 'User already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)

    if role == 'student':
        if not all([student_id, department, year]):
            return Response({'error': 'Student ID is required for students.'}, status=status.HTTP_400_BAD_REQUEST)
        Student.objects.create(user=user, student_id=student_id, department=department, year=year)
    elif role == 'teacher':
        Teacher.objects.create(user=user)
    else:
        return Response({'error': 'Invalid role.'}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)




@api_view(['POST'])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(username=user.username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        role = "student" if hasattr(user, "student") else "teacher"
        
        return Response({
            "message": "Login successful",
        "user": {
            "first_name": user.first_name,
            "email": user.email,
            "role": role,
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)



@api_view(['POST'])
def admin_login(request):
    serializer = AdminLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data, error = admin_login_service(
        serializer.validated_data["email"],
        serializer.validated_data["password"]
    )

    if error:
        return Response({"error": error}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_qr(request):
    try:
        teacher = Teacher.objects.get(user=request.user)

        qr_session = QRCodeSession.objects.create(teacher=teacher)

        return Response({
            "message": "QR code session created",
            "code": qr_session.code,
            "session_id": qr_session.id,
        }, status=status.HTTP_201_CREATED)
    
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_attendance(request):
    code = request.data.get('code')
    if not code:
        return Response({"error": "session id not provided"}, status=400)
    
    try:
        session = QRCodeSession.objects.get(code=code, is_active=True)

        if timezone.now() > session.created_at + timezone.timedelta(minutes=5):
            return Response({"error": "session expired"}, status=400)
        
        student = Student.objects.get(user=request.user)

        if Attendance.objects.filter(student=student, session=session).exists():
            return Response({"message": "Already marked attendance"}, status=200)
        
        Attendance.objects.create(student=student, session=session)

        return Response({"message": "Attendance marked successfully"}, status=201)
    
    except (QRCodeSession.DoesNotExist, Student.DoesNotExist):
        return Response({"error" : "Invalid qr session or student not found"}, status=404)

    

@api_view(['Post'])
@permission_classes([IsAuthenticated])
def todays_class(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        today = timezone.now().date()

        session = ClassSession.objects.filter(teacher=teacher, date=today).first()

        if not session:
            return Response({"message": "No class found today"}, status=404)
        
        data = {
            "id": session.id,
            "subject": session.subject,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "date": session.date,
            "total_students": session.total_students,
        }
        return Response(data)
    
    except Teacher.DoesNotExist:
        return Response({"message": "Teacher not found"}, status=404)
    

@api_view(['Post'])
@permission_classes([IsAuthenticated])
def teacher_profile(request):
    try:
        teacher = Teacher.objects.get(user = request.user)
        profile = {
            "fullname" : request.user.first_name,
            "email" : request.user.email,
        }
        return Response(profile)
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=404)
    

@api_view(['Post'])
@permission_classes([IsAuthenticated])
def student_profile(request):
    try:
        student = Student.objects.get(user = request.user)
        last_attendance = Attendance.objects.filter(student=student).order_by('-timestamp').first()
        last_attendance_date = last_attendance.timestamp.date() if last_attendance else None

        profile = {
            "fullname" : request.user.first_name,
            "email" : request.user.email,
            "id" : student.student_id,
            "department" : student.department,
            "year" : student.year,
            "last_attendance_date": last_attendance_date,
        }
        return Response(profile)
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_history(request):
    try:
        teacher = Teacher.objects.get(user= request.user)
        sessions = ClassSession.objects.filter(teacher=teacher).order_by('-date')
        data = []

        for class_session in sessions:
            qr_session = QRCodeSession.objects.filter(teacher=teacher, created_at__date = class_session.date)
            present = Attendance.objects.filter(session__in=qr_session).count()
            total_students = class_session.total_students or 0
            percentage = (present / total_students ) * 100 if total_students > 0 else 0

            data.append({
                "id": class_session.id,
                "subject": class_session.subject,
                "date": class_session.date,
                "total": total_students,
                "attendees": present,
                "percentage": int(percentage),
            })
        return Response(data)
        
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAdminUser]) 
def admin_attendance_history(request):
    try:
        sessions = ClassSession.objects.all().order_by('-date')
            
        data = []
        for class_session in sessions:
            qr_session = QRCodeSession.objects.filter(
                teacher=class_session.teacher, 
                created_at__date=class_session.date
            )
            present = Attendance.objects.filter(session__in=qr_session).count()
            total_students = class_session.total_students or 0
            percentage = (present / total_students) * 100 if total_students > 0 else 0

            data.append({
                "id": class_session.id,
                "subject": class_session.subject,
                "date": class_session.date,
                "teacher": class_session.teacher.user.get_full_name(),
                "time": class_session.start_time,
                "percentage": int(percentage),
            })
        return Response(data)
        
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=404)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def today_attendance_history(request):
    today = timezone.now().date()  
    try:
        sessions = ClassSession.objects.filter(date=today).order_by('-start_time')
        data = []
        
        for class_session in sessions:
            qr_session = QRCodeSession.objects.filter(
                teacher=class_session.teacher,
                created_at__date=today
            )
            present = Attendance.objects.filter(
                session__in=qr_session,
                timestamp__date=today
            ).count()
            
            total_students = class_session.total_students or 0
            percentage = (present / total_students) * 100 if total_students > 0 else 0

            data.append({
                "id": class_session.id,
                "subject": class_session.subject,
                "start_time": class_session.start_time,
                "end_time": class_session.end_time,
                "teacher": class_session.teacher.user.get_full_name(),
                "time": class_session.start_time,
                "percentage": int(percentage),
                "status": "Ongoing" if timezone.now().time() < class_session.end_time else "Completed"
            })
            
        return Response(data)
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_atten(request, session_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
        class_session = ClassSession.objects.get(teacher=teacher, id=session_id)
        all_students = Student.objects.all()  
        qr_session = QRCodeSession.objects.filter(teacher=teacher, created_at__date=class_session.date)
        attendance_records = Attendance.objects.filter(session__in=qr_session).select_related('student__user')

        present_student_ids = [record.student.id for record in attendance_records]

        student_data = []
        for student in all_students:
            student_data.append({
                "id": student.student_id,
                "name": student.user.first_name,
                "email": student.user.email,
                "time": next(
                    (record.timestamp for record in attendance_records if record.student == student),
                    None
                ),
                "status": "Present" if student.id in present_student_ids else "Absent"
            })

        return Response({"students": student_data})
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=404)
    except ClassSession.DoesNotExist:
        return Response({"error": "Class session not found"}, status=404)
  
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance(request):
    try:
        student = Student.objects.get(user=request.user)
        class_session = ClassSession.objects.all().order_by('-date')

        data = []

        for session in class_session:
            qr_session = QRCodeSession.objects.filter(teacher = session.teacher, created_at__date = session.date)
            attendance = Attendance.objects.filter(student = student, session__in=qr_session).first()

            data.append({
                "id": session.id,
                "date": session.date,
                "subject" : session.subject,
                "status": "present" if attendance else "absent"
            })
        return Response({"attendance_history" : data})
    except ClassSession.DoesNotExist:
        return Response({"error": "Class session not found"}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])  # Change to IsAdminUser
def student_atten_admin(request, student_id):
    try:
        student = Student.objects.select_related('user').get(student_id=student_id)
        class_sess = ClassSession.objects.select_related('teacher__user').all().order_by('date')

        data = []
        for session in class_sess:
            qr_sess = QRCodeSession.objects.filter(teacher=session.teacher, created_at__date=session.date)
            attendance = Attendance.objects.filter(
                student=student, 
                session__in=qr_sess
            ).select_related('session').first()

            data.append({
                "id": session.id,
                "date": session.date.strftime("%Y-%m-%d"),  
                "subject": session.subject,
                "teacher": session.teacher.user.get_full_name(),
                "status": "present" if attendance else "absent",
                "time": attendance.timestamp.strftime("%H:%M") if attendance else None
            })
        return Response({"attendance_history": data})
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Alerts(request):
    try:
        student = Student.objects.get(user=request.user)
        alert = StudentAlert.objects.filter(student=student).order_by('created_at')

        data = []

        for alerts in alert:
            data.append({
                "subject":alerts.subject,
                "message": alerts.message,
                "date": alerts.created_at,
                "is_read":alerts.is_read,
                "title":alerts.title,
                "type": alerts.type
            })
        return Response({"alert":data})
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_atten_percentage(request):
    try:
        student = Student.objects.get(user=request.user)
        session = ClassSession.objects.all().count()
        atten = Attendance.objects.filter(student=student).count()

        percentage = (atten / session) * 100 if session > 0 else 0

        return Response({
            "sessions": session,
            "present": atten,
            "attendance_percentage": round(percentage, 2)
        })   
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def average_attendance_percentage(request):
    try:
        students = Student.objects.all()
        session_count = ClassSession.objects.count()

        total_percentage = 0
        student_count = students.count()

        if session_count == 0 or student_count == 0:
            return Response({"average_attendance": 0.0})

        for student in students:
            attended = Attendance.objects.filter(student=student).count()
            percentage = (attended / session_count) * 100
            total_percentage += percentage

        avg = round(total_percentage / student_count, 2)

        return Response({"average_attendance_percentage": avg})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def streak(request):
    try:
        student = Student.objects.get(user=request.user)
        class_session = ClassSession.objects.order_by('-date')

        streak = 0

        for session in class_session:
            qr_session = QRCodeSession.objects.filter(teacher=session.teacher, created_at__date=session.date)

            attendance = Attendance.objects.filter(student=student, session__in=qr_session).exists()

            if attendance:
                streak += 1
            else:
                break
        return Response({"streak":streak}) 
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)


def atten_percentage(student):
    session = ClassSession.objects.all().count()
    atten = Attendance.objects.filter(student=student).count()
    return round((atten/session) * 100, 2) if session > 0 else 0


@api_view(['GET'])
@permission_classes([IsAdminUser])
def low_attendance_list(request):
    low = []
    stu = Student.objects.select_related('user').all()
    for student in stu:
        percent = atten_percentage(student)
        if percent < 75:
            low.append({
                "id": student.student_id,
                "name":f"{student.user.first_name} {student.user.last_name}",
                "email": student.user.email,
                "semester": student.year,
                "attendance": percent
            })
    return Response(low)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def attendance_list(request):
    data = []
    students = Student.objects.select_related('user').all()
    total_sessions = ClassSession.objects.count() 

    for student in students:
        attended = Attendance.objects.filter(student=student).count()
        percent = round((attended / total_sessions) * 100, 2) if total_sessions > 0 else 0

        data.append({
            "id": student.student_id,
            "name": f"{student.user.first_name} {student.user.last_name}",
            "email": student.user.email,
            "semester": student.year,
            "department": student.department,
            "attendance": percent,
            "presentClasses": attended,
            "totalClasses": total_sessions,
            "attendanceRate": percent 
        })

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def student_detail(request, student_id):
    try:
        student = Student.objects.select_related('user').get(student_id=student_id)
        total_sessions = ClassSession.objects.count()
        attended_records = Attendance.objects.select_related('session').filter(student=student)

        attended = attended_records.count()
        percent = round((attended / total_sessions) * 100, 2) if total_sessions > 0 else 0
        absent = total_sessions - attended

        late_count = 0
        for record in attended_records:
            session_start = record.session.created_at
            late_threshold = session_start + timedelta(minutes=20)
            if record.timestamp > late_threshold:
                late_count += 1

        data = {
            "id": student.student_id,
            "name": f"{student.user.first_name} {student.user.last_name}",
            "email": student.user.email,
            "semester": student.year,
            "department": student.department,
            "attendance": percent,
            "presentClasses": attended,
            "totalClasses": total_sessions,
            "attendanceRate": percent,
            "absent": absent,
            "lateAttendances": late_count,
            "enrollmentDate": student.user.date_joined.strftime("%Y-%m-%d")
        }
        return Response(data)

    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def attendance_by_session(request, class_session_id):
    try:
        class_session = ClassSession.objects.get(id=class_session_id)
        qr_sessions = QRCodeSession.objects.filter(
            teacher=class_session.teacher,
            created_at__date=class_session.date
        )

        
        students = Student.objects.all()
        data = []
        
        for student in students:
            attendance = Attendance.objects.filter(
                student=student,
                session__in=qr_sessions
            ).first()
    
            if attendance:
                late_threshold = attendance.session.created_at + timedelta(minutes=20)
                status = "late" if attendance.timestamp > late_threshold else "present"
                checkin_time = attendance.timestamp.strftime("%H:%M")
            else:
                status = "absent"
                checkin_time = None
        
            data.append({
                "id": student.id,
                "name": f"{student.user.first_name} {student.user.last_name}",
                "studentId": student.student_id,
                "status": status,
                "checkinTime": checkin_time
            })

            
        return Response({"students": data})
        
    except ClassSession.DoesNotExist:
        return Response({"error": "Class session not found"}, status=404)
    


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_class_session(request):
    try:
        teacher_id = request.data.get('teacher_id')
        subject = request.data.get('subject')
        start_time = request.data.get('start_time')   
        end_time = request.data.get('end_time')      
        date = request.data.get('date')              
        total_students = request.data.get('total_students')

        if not all([teacher_id, subject, start_time, end_time, date, total_students]):
            return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)

        session = ClassSession.objects.create(
            teacher=teacher,
            subject=subject,
            start_time=start_time,
            end_time=end_time,
            date=date,
            total_students=total_students
        )
        return Response({
            "message": "Class session created successfully",
            "session_id": session.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_all_teachers(request):
    teachers = Teacher.objects.select_related('user').all()
    data = [
        {
            "id": t.id,
            "name": f"{t.user.first_name} {t.user.last_name}",
            "email": t.user.email,
            "department": t.department,
            "phone": t.phone_number,
            "status": t.status,
            "subject": t.subject
        } for t in teachers
    ]
    return Response(data)



@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_class_sessions(request):
    teacher_id = request.GET.get("teacher_id")
    sessions = get_class_sessions(teacher_id)
    serializer = ClassSessionSerializer(sessions, many=True)
    return Response(serializer.data)



@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_class_session(request, session_id):
    try:
        session = ClassSession.objects.get(id=session_id)
        session.delete()
        return Response({"message": "Class session deleted successfully"})
    except ClassSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def total_teacher(request):
    teac = []
    teachrs = Teacher.objects.select_related('user').all()
    for t in teachrs:
        teac.append({
            "name": f"{t.user.first_name} {t.user.last_name}",
            "email": t.user.email
        })
    return Response (teac)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def total_stu(request):
    stu = []
    student = Student.objects.select_related('user').all()
    for s in student:
        stu.append({
            "name": f"{s.user.first_name} {s.user.last_name}",
            "email": s.user.email,
            "department": s.department
        })
    return Response (stu)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def total_departments(request):
    departments = Student.objects.values_list('department', flat=True).distinct()
    return Response({
        "count": departments.count(),
        "departments": list(departments)
    })



@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_teacher(request, teacher_id):
    try:
        teacher = Teacher.objects.get(id=teacher_id)

        teacher.user.first_name = request.data.get("name", teacher.user.first_name)
        teacher.user.email = request.data.get("email", teacher.user.email)
        teacher.user.save()

        teacher.phone_number = request.data.get("phone_number", teacher.phone_number)
        teacher.department = request.data.get("department", teacher.department)
        teacher.subject = request.data.get("subject", teacher.subject)
        teacher.status = request.data.get("status", teacher.status)  


        teacher.save()

        return Response({"message": "Teacher updated successfully"})
    
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=404)
    

@api_view(['GET'])
@permission_classes([IsAdminUser])
def average_attendance_today(request):
    try:
        today = date.today()
        class_sessions = ClassSession.objects.filter(date=today)

        total_expected = 0
        total_attended = 0

        for session in class_sessions:
            qr_sessions = QRCodeSession.objects.filter(
                teacher=session.teacher,
                created_at__date=session.date
            )

            attended_students = Student.objects.filter(
                attendance__session__in=qr_sessions
            ).distinct()

            total_expected += session.total_students
            total_attended += attended_students.count()

            total_absent = total_expected - total_attended

        average = round((total_attended / total_expected) * 100, 2) if total_expected > 0 else 0

        return Response({
            "date": today.strftime("%Y-%m-%d"),
            "total_sessions": class_sessions.count(),
            "total_students_expected": total_expected,
            "total_students_attended": total_attended,
            "average_attendance_percentage": average,
            "total_absent": total_absent
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
@api_view(['GET'])
@permission_classes([IsAdminUser])
def weekly_attendance_trend(request):
    try:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

        trend_data = []

        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            class_session = ClassSession.objects.filter(date=current_day)

            total_expected = 0
            total_present = 0

            for session in class_session:
                qr_session = QRCodeSession.objects.filter(teacher = session.teacher, created_at__date = current_day)

                attended_students = Student.objects.filter(
                attendance__session__in=qr_session
                ).distinct()

                total_expected += session.total_students
                total_present += attended_students.count()

            percentage = round((total_present / total_expected) * 100, 2) if total_expected > 0 else 0
            trend_data.append({
                "day": current_day.strftime("%a"),
                "attendance": percentage
            })
        return Response(trend_data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

SUBJECT_COLORS = [
    "#3B82F6", "#F59E0B", "#10B981", "#EF4444", "#8B5CF6", "#EC4899", "#22D3EE"
]

@api_view(['GET'])
@permission_classes([IsAdminUser])
def subject_wise_attendance(request):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    subject = {}

    for i in range(7):
        current_day = start_of_week + timedelta(days=i)
        sessions = ClassSession.objects.filter(date=current_day)

        for session in sessions:
            sub = session.subject
            qr_sessions = QRCodeSession.objects.filter(teacher=session.teacher, created_at__date = current_day)

            attended_student = Student.objects.filter(attendance__session__in=qr_sessions).distinct()

            expected = session.total_students
            present = attended_student.count()

            if sub not in subject:
                subject[sub] = {"present": 0, "expected": 0}
            subject[sub]["present"] += present
            subject[sub]["expected"] += expected
    result = []
    for i, (sub, stats) in enumerate(subject.items()):
        expected = stats["expected"]
        present = stats["present"]
        percentage = round((present / expected) * 100, 2) if expected > 0 else 0

        result.append({
            "name": subject,
            "value": percentage,
            "color": SUBJECT_COLORS[i % len(SUBJECT_COLORS)]
        })

    return Response(result)

# @api_view(['POST'])
# @permission_classes([IsAdminUser])
# def send_alerts(request):
#     students = request.data.get('students', [])
#     count = 0

#     for s in students:
#         sid = s.get('id')
#         pct = s.get('attendance')
#         print(f"Processing student ID: {sid}, attendance: {pct}")  

#         if sid is None or pct is None:
#             continue

#         try:
#             student = Student.objects.get(student_id=sid)
#         except Student.DoesNotExist:
#             print(f"Student not found: {sid}") 
#             continue

#         if pct < 60:
#             level = 'warning'
#             msg = "⚠️ Critical alert: your attendance is below 60%. Immediate action required!"
#         elif pct < 70:
#             level = 'info'
#             msg = "Your attendance is below 70%. Please improve it soon."
#         else:
#             level = 'success'
#             msg = "Your attendance is below 75%. You're at risk—please increase your attendance."
        
#         StudentAlert.objects.create(
#             student=student,
#             title="Attendance Alert!",
#             subject="Attendance Notification",
#             message=msg,
#             type=level
#         )
#         count += 1

#     return Response({"alerts_sent": count}, status=status.HTTP_201_CREATED)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "rs0036870@gmail.com"
SENDER_PASSWORD = "oirb gaqk oxig oaha"

def send_email(to_email, subject, template_name, context):
    template_path = os.path.abspath(f"Atten_app/templates/{template_name}.html")
    with open(template_path, "r", encoding="utf-8") as file:
        template_str = file.read()

    jinja_template = Template(template_str)
    email_content = jinja_template.render(context)

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(email_content, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_alerts(request):
    students = request.data.get('students', [])
    count = 0

    for s in students:
        sid = s.get('id')
        pct = s.get('attendance')

        if sid is None or pct is None:
            continue

        try:
            student = Student.objects.get(student_id=sid)
        except Student.DoesNotExist:
            continue

        if pct < 60:
            level = 'warning'
            msg = "⚠️ Critical alert: your attendance is below 60%. Immediate action required!"
        elif pct < 70:
            level = 'info'
            msg = "Your attendance is below 70%. Please improve it soon."
        else:
            level = 'success'
            msg = "Your attendance is below 75%. You're at risk—please increase your attendance."
        
        StudentAlert.objects.create(
            student=student,
            title="Attendance Alert!",
            subject="Attendance Notification",
            message=msg,
            type=level
        )
        count += 1

        email_context = {
            "name": student.user.first_name,
            "subject": student.year,
            "attendance_rate": round(pct, 2),
            "sender_name": "AttenQR Team"
        }

        send_email(
            to_email=student.user.email,
            subject="📢 Attendance Alert from AttenQR",
            template_name="index",
            context=email_context
        )


    return Response({"alerts_sent": count}, status=status.HTTP_201_CREATED)





# send_email(
#     to_email="ranjesh.thakur@aitm.edu.np",
#     subject="Attendance Alert",
#     template_name="index",
#     context={
#         "name": "Ranjesh",
#         "subject": "Data Structures",
#         "attendance_rate": 65,
#         "sender_name": "AttenQR Team",
#     },
# )
