from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    RegisterSerializer, 
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    ResendVerificationEmailSerializer
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    API view for user registration with email verification.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        self.send_verification_email(user)
        
        return Response({
            "message": "User registered successfully. Please check your email to verify your account.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, user):
        """
        Send verification email to the user.
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'Plum Classification System',
            'expiration_hours': 48
        }
        
        html_message = render_to_string('authentication/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Verify your email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )


class VerifyEmailView(APIView):
    """
    API view for email verification.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        user = User.objects.filter(email_verification_token=token).first()
        
        if not user:
            return Response({"error": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Activate user and mark email as verified
        user.is_active = True
        user.email_verified = True
        user.email_verification_token = None
        user.save()
        
        return Response({
            "message": "Email verified successfully. You can now log in.",
            "email": user.email
        }, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """
    API view for resending verification email.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if user.email_verified:
            return Response({"message": "Email is already verified."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new verification token
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Send verification email
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.email_verification_token}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'Plum Classification System',
            'expiration_hours': 48
        }
        
        html_message = render_to_string('authentication/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Verify your email address',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        return Response({
            "message": "Verification email resent successfully. Please check your email."
        }, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses the enhanced token serializer.
    """
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """
    API view for user logout.
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API view for changing password.
    """
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    API view for requesting password reset.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        
        if user:
            # Generate password reset token
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            # Send password reset email
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            
            context = {
                'user': user,
                'reset_url': reset_url,
                'site_name': 'Plum Classification System',
                'expiration_hours': 24
            }
            
            html_message = render_to_string('authentication/password_reset_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject='Reset your password',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
        
        # Always return success to prevent email enumeration
        return Response({
            "message": "If an account with this email exists, a password reset link has been sent."
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API view for confirming password reset.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid user ID."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check token validity
        if not default_token_generator.check_token(user, serializer.validated_data['token']):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password reset successful. You can now log in with your new password."}, 
                        status=status.HTTP_200_OK)
