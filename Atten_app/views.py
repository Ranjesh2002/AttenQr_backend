from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student, Teacher, QRCodeSession, Attendance
from django.utils import timezone

@api_view(['POST'])
def register_user(request):
    data = request.data

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    student_id = data.get('studentId')

    if not all([name, email, password, role]):
        return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'error': 'User already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)

    if role == 'student':
        if not student_id:
            return Response({'error': 'Student ID is required for students.'}, status=status.HTTP_400_BAD_REQUEST)
        Student.objects.create(user=user, student_id=student_id)
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
        refresh = RefreshToken.for_user(user)  # Generate tokens
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
        user = request.user
        teacher = Teacher.objects.get(user=user)

        qr_session = QRCodeSession.objects.create(teacher=teacher)

        return Response({
            "message": "QR code session created",
            "code": qr_session.code,
            "session_id": qr_session.id,
        }, status=status.HTTP_201_CREATED)
    
    except Teacher.DoesNotExist:
        return Response({"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

#api for marking attendance using QR code
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_attendance(request):
    code = request.data.get('code')
    if not code:
        return Response({"error": "session id not provided"}, status=400)
    
    try:
        session = QRCodeSession.objects.get(code=code, is_active=True)

        if timezone.now() > session.created_at + timezone.timedelta(minutes=10):
            return Response({"error": "session expired"}, status=400)
        
        student = Student.objects.get(user=request.user)

        if Attendance.objects.filter(student=student, session=session).exists():
            return Response({"message": "Already marked attendance"}, status=200)
        
        Attendance.objects.create(student=student, session=session)

        return Response({"message": "Attendance marked successfully"}, status=201)
    
    except QRCodeSession.DoesNotExist:
        return Response({"error" : "Invalid or expired qr session"}, status=404)
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
