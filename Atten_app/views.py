from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from .models import Student, Teacher

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


# attendance/views.py


class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Find the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        # Authenticate using username (since Django uses username internally)
        user = authenticate(username=user.username, password=password)

        if user is not None:
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
