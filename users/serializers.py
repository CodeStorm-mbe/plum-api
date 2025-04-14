from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.validators import UniqueValidator
from .models import Farm, UserSettings

User = get_user_model()


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle UserSettings avec validation améliorée.
    """
    class Meta:
        model = UserSettings
        fields = (
            'id', 'user', 'notification_preferences', 'ui_preferences',
            'language', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate_notification_preferences(self, value):
        """Valide que les préférences de notification ont un format correct."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Les préférences de notification doivent être un objet JSON."))
        
        # Vérifier les clés autorisées
        allowed_keys = {'email', 'push', 'sms'}
        for key in value:
            if key not in allowed_keys:
                raise serializers.ValidationError(_(f"Clé non autorisée: {key}. Les clés autorisées sont: {', '.join(allowed_keys)}"))
            
            # Vérifier que les valeurs sont des booléens
            if not isinstance(value[key], bool):
                raise serializers.ValidationError(_(f"La valeur pour {key} doit être un booléen."))
        
        return value
    
    def validate_ui_preferences(self, value):
        """Valide que les préférences d'interface ont un format correct."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Les préférences d'interface doivent être un objet JSON."))
        
        # Vérifier les thèmes autorisés
        if 'theme' in value and value['theme'] not in ['light', 'dark', 'system']:
            raise serializers.ValidationError(_("Thème non valide. Les thèmes autorisés sont: light, dark, system."))
        
        # Vérifier les dispositions de tableau de bord autorisées
        if 'dashboard_layout' in value and value['dashboard_layout'] not in ['grid', 'list', 'compact']:
            raise serializers.ValidationError(_("Disposition non valide. Les dispositions autorisées sont: grid, list, compact."))
        
        # Vérifier que items_per_page est un entier positif
        if 'items_per_page' in value:
            try:
                items = int(value['items_per_page'])
                if items <= 0 or items > 100:
                    raise serializers.ValidationError(_("Le nombre d'éléments par page doit être entre 1 et 100."))
            except (ValueError, TypeError):
                raise serializers.ValidationError(_("Le nombre d'éléments par page doit être un entier."))
        
        return value
    
    def create(self, validated_data):
        """Crée et retourne des paramètres utilisateur, en définissant l'utilisateur au utilisateur actuel."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class FarmSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Farm avec validation améliorée et champs calculés.
    """
    owner_username = serializers.ReadOnlyField(source='owner.username')
    owner_email = serializers.ReadOnlyField(source='owner.email')
    coordinates = serializers.SerializerMethodField()
    has_location_data = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Farm
        fields = (
            'id', 'name', 'location', 'size', 'owner', 'owner_username', 'owner_email',
            'description', 'latitude', 'longitude', 'coordinates', 'has_location_data',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'owner', 'owner_username', 'owner_email', 'created_at', 'updated_at')
    
    def get_coordinates(self, obj):
        """Retourne les coordonnées de la ferme sous forme de tuple (latitude, longitude)."""
        return obj.coordinates
    
    def validate(self, data):
        """Valide que les coordonnées sont cohérentes."""
        # Si une seule coordonnée est fournie, l'autre doit l'être aussi
        if ('latitude' in data and 'longitude' not in data) or ('longitude' in data and 'latitude' not in data):
            raise serializers.ValidationError(_("Les coordonnées de latitude et longitude doivent être fournies ensemble."))
        
        return data
    
    def validate_size(self, value):
        """Valide que la taille est positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError(_("La taille de la ferme doit être positive."))
        return value
    
    def create(self, validated_data):
        """Crée et retourne une nouvelle ferme, en définissant le propriétaire à l'utilisateur actuel."""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle User personnalisé avec validation améliorée.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        min_length=8,
        help_text=_("Le mot de passe doit contenir au moins 8 caractères.")
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text=_("L'adresse email doit être unique.")
    )
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'confirm_password', 'first_name',
            'last_name', 'full_name', 'role', 'phone_number', 'profile_image', 'organization',
            'address', 'email_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'email_verified', 'created_at', 'updated_at')
        extra_kwargs = {
            'username': {
                'validators': [UniqueValidator(queryset=User.objects.all())],
                'help_text': _("Le nom d'utilisateur doit être unique.")
            },
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, data):
        """Vérifie que les mots de passe correspondent."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": _("Les mots de passe ne correspondent pas.")})
        
        # Vérification de la complexité du mot de passe
        password = data.get('password')
        if password:
            # Vérifier la présence de lettres
            if not any(char.isalpha() for char in password):
                raise serializers.ValidationError({"password": _("Le mot de passe doit contenir au moins une lettre.")})
            
            # Vérifier la présence de chiffres
            if not any(char.isdigit() for char in password):
                raise serializers.ValidationError({"password": _("Le mot de passe doit contenir au moins un chiffre.")})
        
        return data
    
    def validate_role(self, value):
        """Vérifie que le rôle est valide."""
        valid_roles = [choice[0] for choice in User.Roles.choices]
        if value not in valid_roles:
            raise serializers.ValidationError(
                _("Rôle non valide. Les rôles autorisés sont: {}.").format(", ".join(valid_roles))
            )
        
        # Seuls les administrateurs peuvent créer d'autres administrateurs
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            if value == User.Roles.ADMIN and not (request.user.is_admin_user or request.user.is_superuser):
                raise serializers.ValidationError(_("Vous n'avez pas l'autorisation de créer un administrateur."))
        
        return value
    
    def create(self, validated_data):
        """Crée et retourne un nouvel utilisateur avec mot de passe chiffré."""
        # Supprimer confirm_password des données
        validated_data.pop('confirm_password', None)
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data.pop('password'),
            **validated_data
        )
        
        return user
    
    def update(self, instance, validated_data):
        """Met à jour et retourne un utilisateur existant."""
        # Supprimer password et confirm_password des données si non fournis
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        # Mettre à jour les champs de l'utilisateur
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Mettre à jour le mot de passe si fourni
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations de profil utilisateur avec relations imbriquées.
    """
    farms = FarmSerializer(many=True, read_only=True)
    settings = UserSettingsSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'phone_number', 'profile_image', 'organization',
            'address', 'email_verified', 'farms', 'settings', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'username', 'email', 'role', 'email_verified', 
            'created_at', 'updated_at'
        )
    
    def to_representation(self, instance):
        """Personnalise la représentation du profil utilisateur."""
        representation = super().to_representation(instance)
        
        # Ajouter le nombre de fermes
        representation['farms_count'] = instance.farms.count()
        
        # Ajouter la date de dernière connexion
        representation['last_login'] = instance.last_login.isoformat() if instance.last_login else None
        
        return representation
