"""
Vues pour l'authentification JWT et la gestion des utilisateurs.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status, permissions
import uuid
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import CreateAPIView

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    VerifyEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)
from .models import EmailVerificationToken, PasswordResetToken
from .services import EmailService

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée pour obtenir les tokens JWT.
    Remplace la vue standard de Simple JWT pour ajouter des informations supplémentaires.
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(CreateAPIView):
    """
    Vue pour l'inscription des utilisateurs.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer


class VerifyEmailView(APIView):
    """
    Vue pour vérifier l'email d'un utilisateur.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            
            try:
                token = EmailVerificationToken.objects.get(token=token_value)
                user = token.user
                
                # Marquer l'email comme vérifié
                user.email_verified = True
                user.save()
                
                # Marquer le token comme utilisé
                token.is_used = True
                token.save()
                
                return Response(
                    {"detail": _("Email vérifié avec succès.")},
                    status=status.HTTP_200_OK
                )
            except EmailVerificationToken.DoesNotExist:
                return Response(
                    {"detail": _("Token invalide.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """
    Vue pour renvoyer l'email de vérification.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"detail": _("L'email est requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            
            # Vérifier si l'email est déjà vérifié
            if user.email_verified:
                return Response(
                    {"detail": _("L'email est déjà vérifié.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer un nouveau token
            token = EmailVerificationToken.objects.create(
                user=user,
                token=uuid.uuid4(),
                expires_at=timezone.now() + timezone.timedelta(days=1)
            )
            
            # Construire l'URL de vérification
            verification_url = f"/api/users/verify-email/{token.token}/"
            
            # Envoyer l'email de vérification
            EmailService.send_verification_email(user, verification_url)
            
            return Response(
                {"detail": _("Email de vérification envoyé.")},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas révéler si l'email existe ou non
            return Response(
                {"detail": _("Si l'email existe, un email de vérification a été envoyé.")},
                status=status.HTTP_200_OK
            )


class PasswordResetRequestView(APIView):
    """
    Vue pour demander une réinitialisation de mot de passe.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Créer un token de réinitialisation
                token = PasswordResetToken.objects.create(
                    user=user,
                    token=uuid.uuid4(),
                    expires_at=timezone.now() + timezone.timedelta(hours=24)
                )
                
                # Construire l'URL de réinitialisation
                reset_url = f"/reset-password/{token.token}/"
                
                # Envoyer l'email de réinitialisation
                EmailService.send_password_reset_email(user, reset_url)
            except User.DoesNotExist:
                # Pour des raisons de sécurité, ne pas révéler si l'email existe ou non
                pass
            
            return Response(
                {"detail": _("Si l'email existe, un email de réinitialisation a été envoyé.")},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Vue pour confirmer la réinitialisation de mot de passe.
    """
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                token = PasswordResetToken.objects.get(token=token_value)
                
                # Vérifier si le token est expiré
                if token.is_expired:
                    return Response(
                        {"detail": _("Token expiré.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Vérifier si le token a déjà été utilisé
                if token.is_used:
                    return Response(
                        {"detail": _("Token déjà utilisé.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                user = token.user
                
                # Changer le mot de passe
                user.set_password(password)
                user.save()
                
                # Marquer le token comme utilisé
                token.is_used = True
                token.save()
                
                return Response(
                    {"detail": _("Mot de passe réinitialisé avec succès.")},
                    status=status.HTTP_200_OK
                )
            except PasswordResetToken.DoesNotExist:
                return Response(
                    {"detail": _("Token invalide.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
