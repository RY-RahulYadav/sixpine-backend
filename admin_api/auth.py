from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from accounts.serializers import UserSerializer
from .utils import create_admin_log

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login_view(request):
    """
    Admin-specific login endpoint that requires staff privileges.
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    print(f"Admin login attempt - Username: {username}")
    
    if not username or not password:
        print("Error: Missing username or password")
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if not user:
        print(f"Error: Authentication failed for username: {username}")
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_staff:
        print(f"Error: User {username} is not staff")
        return Response(
            {'error': 'Access denied. Admin privileges required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    token, _ = Token.objects.get_or_create(user=user)
    
    # Log admin login
    try:
        create_admin_log(
            request=request,
            action_type='login',
            model_name='User',
            object_id=user.id,
            object_repr=f'{user.username} (Admin Login)',
            details={'username': user.username, 'email': user.email}
        )
    except Exception as e:
        print(f"Error creating admin log: {e}")
    
    print(f"Success: Admin login for {username}")
    
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
        'message': 'Admin login successful'
    })