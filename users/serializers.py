from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Farm, UserSettings

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom User model.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'confirm_password', 'first_name', 
                  'last_name', 'role', 'phone_number', 'profile_image', 'organization', 
                  'address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        """
        Check that the passwords match.
        """
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
        return data
    
    def create(self, validated_data):
        """
        Create and return a new user with encrypted password.
        """
        # Remove confirm_password from the data
        validated_data.pop('confirm_password', None)
        
        # Create the user
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
        )
        
        # Create default user settings
        UserSettings.objects.create(user=user)
        
        return user
    
    def update(self, instance, validated_data):
        """
        Update and return an existing user.
        """
        # Remove password and confirm_password from the data if not provided
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        # Update the user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class FarmSerializer(serializers.ModelSerializer):
    """
    Serializer for the Farm model.
    """
    owner_username = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Farm
        fields = ('id', 'name', 'location', 'size', 'owner', 'owner_username', 
                  'description', 'latitude', 'longitude', 'created_at', 'updated_at')
        read_only_fields = ('id', 'owner', 'owner_username', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Create and return a new farm, setting the owner to the current user.
        """
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserSettings model.
    """
    class Meta:
        model = UserSettings
        fields = ('id', 'user', 'notification_preferences', 'ui_preferences', 
                  'language', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Create and return user settings, setting the user to the current user.
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    farms = FarmSerializer(many=True, read_only=True)
    settings = UserSettingsSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 
                  'phone_number', 'profile_image', 'organization', 'address', 
                  'farms', 'settings', 'created_at', 'updated_at')
        read_only_fields = ('id', 'username', 'email', 'role', 'created_at', 'updated_at')
