from rest_framework import serializers
from .models import ClassSession, Student, Parent, ParentMessage, Attendance


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class ParentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ClassSessionSerializer(serializers.ModelSerializer):
    teacher = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = ["id", "subject", "teacher", "date", "start_time", "end_time", "total_students"]

    def get_teacher(self, obj):
        return f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}"
    

class StudentProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.first_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Student
        fields = ['student_id', 'department', 'year', 'name', 'email']

class ParentProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.first_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    student = StudentProfileSerializer(read_only=True)

    class Meta:
        model = Parent
        fields = ['name', 'email', 'phone_number', 'student']


class ParentMessageSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = ParentMessage
        fields = ["id", "title", "content", "type", "sender","is_read", "priority", "date"]

    def get_date(self, obj):
        return obj.created_at.strftime("%b %d, %Y %I:%M %p")


class AttendanceSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'date', 'timestamp']

    def get_date(self, obj):
        return obj.timestamp.date()