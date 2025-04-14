"""
Configuration des URLs pour l'application users.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView
)

app_name = 'users'

urlpatterns = [
    # Authentification JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Inscription et vérification d'email
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification-email/', ResendVerificationEmailView.as_view(), name='resend_verification_email'),
    
    # Réinitialisation de mot de passe
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
