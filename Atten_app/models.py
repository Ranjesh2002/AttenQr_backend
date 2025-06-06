from django.db import models
from django.contrib.auth.models import User
import uuid

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.user.first_name} (Student)"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.first_name} (Teacher)"


class QRCodeSession(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"QR Session by {self.teacher.user.first_name} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(QRCodeSession, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"{self.student.user.first_name} - Present at {self.timestamp.strftime('%H:%M')}"
