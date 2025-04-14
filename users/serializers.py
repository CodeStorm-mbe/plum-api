"""
Sérialiseurs pour l'authentification JWT.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from datetime import timedelta
import uuid

from users.models import EmailVerificationToken
from users.services import EmailService

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Sérialiseur personnalisé pour les tokens JWT avec des informations supplémentaires.
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Ajoute des claims personnalisés au token JWT.
        """
        token = super().get_token(user)
        
        # Ajouter des claims personnalisés
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.get_full_name()
        token['is_verified'] = user.email_verified
        
        return token
    
    def validate(self, attrs):
        """
        Vérifie que l'utilisateur est actif et que son email est vérifié.
        """
        data = super().validate(attrs)
        
        # Vérifier si l'email est vérifié
        if not self.user.email_verified:
            raise serializers.ValidationError(
                _("Votre email n'a pas été vérifié. Veuillez vérifier votre boîte de réception.")
            )
        
        # Ajouter des informations supplémentaires à la réponse
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'full_name': self.user.get_full_name(),
            'role': self.user.role,
            'is_verified': self.user.email_verified
        }
        
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription des utilisateurs.
    """
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 'role', 'phone_number')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """
        Vérifie que les mots de passe correspondent.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": _("Les mots de passe ne correspondent pas.")}
            )
        
        return attrs
    
    def create(self, validated_data):
        """
        Crée un nouvel utilisateur avec les données validées.
        """
        # Supprimer le champ password2
        validated_data.pop('password2')
        
        # Créer l'utilisateur
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', User.AGRICULTEUR),
            phone_number=validated_data.get('phone_number', ''),
            is_active=True,
            email_verified=False  # L'email doit être vérifié
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        # Créer un token de vérification d'email
        token = EmailVerificationToken.objects.create(
            user=user,
            token=uuid.uuid4(),
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        # Construire l'URL de vérification (à adapter selon l'environnement)
        verification_url = f"/api/users/verify-email/{token.token}/"
        
        # Envoyer l'email de vérification
        EmailService.send_verification_email(user, verification_url)
        
        return user


class VerifyEmailSerializer(serializers.Serializer):
    """
    Sérialiseur pour la vérification d'email.
    """
    token = serializers.UUIDField(required=True)
    
    def validate_token(self, value):
        """
        Vérifie que le token existe, n'est pas expiré et n'a pas déjà été utilisé.
        """
        try:
            token = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError(_("Token invalide."))
        
        if token.is_expired:
            raise serializers.ValidationError(_("Token expiré."))
        
        if token.is_used:
            raise serializers.ValidationError(_("Token déjà utilisé."))
        
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Sérialiseur pour la demande de réinitialisation de mot de passe.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Vérifie que l'email correspond à un utilisateur existant.
        """
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas révéler si l'email existe ou non
            pass
        
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Sérialiseur pour la confirmation de réinitialisation de mot de passe.
    """
    token = serializers.UUIDField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """
        Vérifie que les mots de passe correspondent et que le token est valide.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": _("Les mots de passe ne correspondent pas.")}
            )
        
        return attrs
