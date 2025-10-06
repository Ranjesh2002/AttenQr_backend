from django.contrib import admin
from .models import Student, Teacher, Parent, QRCodeSession,  Attendance, ClassSession, StudentAlert, ParentMessage

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Parent)
admin.site.register(QRCodeSession)
admin.site.register(Attendance)
admin.site.register(ClassSession)
admin.site.register(StudentAlert)
admin.site.register(ParentMessage)
