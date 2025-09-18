from rest_framework import serializers
from .models import ClassSession


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