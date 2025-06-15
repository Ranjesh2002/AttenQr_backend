from django.contrib import admin
from .models import Student, Teacher, QRCodeSession,  Attendance, ClassSession

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(QRCodeSession)
admin.site.register(Attendance)
admin.site.register(ClassSession)
