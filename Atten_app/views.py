from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student, Teacher, QRCodeSession, Attendance, ClassSession,StudentAlert
from django.utils import timezone

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