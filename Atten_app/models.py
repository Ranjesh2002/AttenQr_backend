from django.db import models
from django.contrib.auth.models import User
import uuid

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=50)
    year = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.first_name} (Student) {self.department} {self.year}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=[("active", "Active"), ("inactive", "Inactive")])
    subject = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.first_name} (Teacher)"
    
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="parent", null=True, blank=True)

    def __str__(self):
        if self.student:
            return f"{self.user.first_name} (Parent of {self.student.user.first_name})"
        return f"{self.user.first_name} (Parent - no student linked)"
    #username: thakur, password: ranjesh123@#



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

class ClassSession(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    start_time = models.TimeField() 
    end_time = models.TimeField()    
    date = models.DateField()
    total_students = models.IntegerField()  

    def __str__(self):
        return f"{self.teacher.user.first_name} - {self.subject} on {self.date}"
    

class StudentAlert(models.Model):
    Alert_type = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('success', 'Success'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=Alert_type, default='info')

    def __str__(self):
        return f"Alert for {self.student.user.first_name} - {self.subject}"



class ParentMessage(models.Model):
    TYPE_CHOICE = [
        ("announcement", "Announcement"),
        ("event", "Event"),
        ("academic", "Academic"),
        ("alert", "Alert"),
    ]

    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name="message")
    title = models.CharField(max_length=200)
    content = models.TextField()
    sender = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICE, default="announcement")
    is_read = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.parent.user.first_name})"