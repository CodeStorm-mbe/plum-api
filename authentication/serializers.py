from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with email verification.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password', 'first_name', 
                  'last_name', 'role', 'phone_number', 'organization', 'address')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, data):
        """
        Validate the registration data.
        """
        # Check that the passwords match
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
        
        # Validate password strength
        try:
            validate_password(data.get('password'))
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        
        # Check if email already exists
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new user with encrypted password and email verification token.
        """
        # Remove confirm_password from the data
        validated_data.pop('confirm_password', None)
        
        # Create the user with is_active=False until email is verified
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'farmer'),
            phone_number=validated_data.get('phone_number', None),
            organization=validated_data.get('organization', None),
            address=validated_data.get('address', None),
            is_active=False  # User will be activated after email verification
        )
        
        # Generate email verification token
        user.generate_email_verification_token()
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        # Create default user settings
        from users.models import UserSettings
        UserSettings.objects.get_or_create(user=user)
        
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """
        Validate that the token exists and is associated with a user.
        """
        user = User.objects.filter(email_verification_token=value).first()
        if not user:
            raise serializers.ValidationError("Invalid verification token.")
        
        # Check if token is expired (48 hours)
        if user.email_verification_sent_at:
            expiration_time = user.email_verification_sent_at + timezone.timedelta(hours=48)
            if timezone.now() > expiration_time:
                raise serializers.ValidationError("Verification token has expired. Please request a new one.")
        
        return value


class ResendVerificationEmailSerializer(serializers.Serializer):
    """
    Serializer for resending verification email.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Validate that the email exists in the system.
        """
        user = User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("No user found with this email address.")
        
        if user.email_verified:
            raise serializers.ValidationError("This email is already verified.")
        
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer to include additional user information in the token response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email_verified'] = user.email_verified
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if email is verified
        if not self.user.email_verified:
            raise serializers.ValidationError(
                {"email": "Email not verified. Please verify your email before logging in."}
            )
        
        # Add extra responses
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = self.user.role
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['email_verified'] = self.user.email_verified
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """
        Validate the password change data.
        """
        # Check that the new passwords match
        if data.get('new_password') != data.get('confirm_new_password'):
            raise serializers.ValidationError({"confirm_new_password": "New passwords don't match."})
        
        # Validate new password strength
        try:
            validate_password(data.get('new_password'))
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        Validate that the email exists in the system.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """
        Validate the password reset confirmation data.
        """
        # Check that the new passwords match
        if data.get('new_password') != data.get('confirm_new_password'):
            raise serializers.ValidationError({"confirm_new_password": "New passwords don't match."})
        
        # Validate new password strength
        try:
            validate_password(data.get('new_password'))
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        
        return data
