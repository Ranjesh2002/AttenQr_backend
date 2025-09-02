from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

def admin_login_service(email, password):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None, "Invalid credentials"

    user = authenticate(username=user.username, password=password)

    if user is None:
        return None, "Invalid credentials"

    if not user.is_superuser:
        return None, "You are not authorized as admin"

    refresh = RefreshToken.for_user(user)

    data = {
        "message": "Admin login successful",
        "user": {
            "first_name": user.first_name,
            "email": user.email,
            "role": "admin",
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    }
    return data, None
