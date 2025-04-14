from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string
from django.conf import settings
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User avec support amélioré pour l'email.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe donnés.
        """
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        if not username:
            raise ValueError(_('Le nom d\'utilisateur est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Créer les paramètres utilisateur par défaut
        # UserSettings.objects.create(user=user)
        
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """
        Crée et sauvegarde un superutilisateur avec l'email et le mot de passe donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec des champs supplémentaires pour le système de classification des prunes.
    Utilise l'email comme identifiant unique et ajoute des rôles spécifiques.
    """
    class Roles(models.TextChoices):
        FARMER = 'farmer', _('Agriculteur')
        TECHNICIAN = 'technician', _('Technicien')
        ADMIN = 'admin', _('Administrateur')
    
    # Champs de base
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    email = models.EmailField(_('adresse email'), unique=True)
    role = models.CharField(
        _('rôle'), 
        max_length=20, 
        choices=Roles.choices, 
        default=Roles.FARMER
    )
    phone_number = models.CharField(_('numéro de téléphone'), max_length=20, blank=True, null=True)
    profile_image = models.ImageField(
        _('image de profil'), 
        upload_to='profile_images/', 
        blank=True, 
        null=True
    )
    
    # Vérification de l'email
    email_verified = models.BooleanField(_('email vérifié'), default=False)
    email_verification_token = models.CharField(
        _('jeton de vérification email'), 
        max_length=100, 
        blank=True, 
        null=True,
        db_index=True  # Indexé pour des recherches plus rapides
    )
    email_verification_sent_at = models.DateTimeField(
        _('date d\'envoi de la vérification email'), 
        blank=True, 
        null=True
    )
    
    # Champs supplémentaires pour les agriculteurs
    organization = models.CharField(_('organisation'), max_length=100, blank=True, null=True)
    address = models.TextField(_('adresse'), blank=True, null=True)
    
    # Horodatage
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('dernière IP de connexion'), blank=True, null=True)
    
    # Configuration
    objects = UserManager()
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['email_verified']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
    
    @property
    def is_farmer(self):
        """Vérifie si l'utilisateur est un agriculteur."""
        return self.role == self.Roles.FARMER
    
    @property
    def is_technician(self):
        """Vérifie si l'utilisateur est un technicien."""
        return self.role == self.Roles.TECHNICIAN
    
    @property
    def is_admin_user(self):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.role == self.Roles.ADMIN
    
    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def generate_email_verification_token(self):
        """Génère un jeton aléatoire pour la vérification de l'email."""
        self.email_verification_token = get_random_string(64)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token
    
    def verify_email(self):
        """Marque l'email comme vérifié et efface le jeton."""
        self.email_verified = True
        self.email_verification_token = None
        self.save(update_fields=['email_verified', 'email_verification_token'])
    
    def token_is_valid(self, max_age_hours=48):
        """Vérifie si le jeton de vérification d'email est encore valide."""
        if not self.email_verification_token or not self.email_verification_sent_at:
            return False
        
        expiration_time = self.email_verification_sent_at + timezone.timedelta(hours=max_age_hours)
        return timezone.now() <= expiration_time


class Farm(models.Model):
    """
    Modèle représentant une ferme appartenant à un utilisateur.
    """
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    name = models.CharField(_('nom'), max_length=100)
    location = models.CharField(_('emplacement'), max_length=255)
    size = models.DecimalField(
        _('taille (hectares)'), 
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='farms',
        verbose_name=_('propriétaire')
    )
    description = models.TextField(_('description'), blank=True, null=True)
    
    # Coordonnées pour l'affichage sur la carte
    latitude = models.DecimalField(
        _('latitude'), 
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True
    )
    longitude = models.DecimalField(
        _('longitude'), 
        max_digits=9, 
        decimal_places=6, 
        blank=True, 
        null=True
    )
    
    # Horodatage
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('ferme')
        verbose_name_plural = _('fermes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    @property
    def coordinates(self):
        """Retourne les coordonnées de la ferme sous forme de tuple (latitude, longitude)."""
        if self.latitude is not None and self.longitude is not None:
            return (float(self.latitude), float(self.longitude))
        return None
    
    @property
    def has_location_data(self):
        """Vérifie si la ferme a des données de localisation."""
        return self.latitude is not None and self.longitude is not None


class UserSettings(models.Model):
    """
    Modèle pour stocker les préférences de l'utilisateur.
    """
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='settings',
        verbose_name=_('utilisateur')
    )
    notification_preferences = models.JSONField(
        _('préférences de notification'), 
        default=dict,
        help_text=_('Préférences pour les notifications par email, SMS, etc.')
    )
    ui_preferences = models.JSONField(
        _('préférences d\'interface'), 
        default=dict,
        help_text=_('Préférences pour l\'interface utilisateur')
    )
    language = models.CharField(
        _('langue'), 
        max_length=10, 
        default='fr',
        choices=[
            ('fr', _('Français')),
            ('en', _('Anglais')),
            ('es', _('Espagnol')),
        ]
    )
    
    # Horodatage
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('paramètres utilisateur')
        verbose_name_plural = _('paramètres utilisateurs')
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Paramètres de {self.user.username}"
    
    @property
    def default_notification_preferences(self):
        """Retourne les préférences de notification par défaut."""
        return {
            'email': True,
            'push': True,
            'sms': False,
        }
    
    @property
    def default_ui_preferences(self):
        """Retourne les préférences d'interface par défaut."""
        return {
            'theme': 'light',
            'dashboard_layout': 'grid',
            'items_per_page': 10,
        }
    
    def save(self, *args, **kwargs):
        """Assure que les préférences par défaut sont définies."""
        if not self.notification_preferences:
            self.notification_preferences = self.default_notification_preferences
        
        if not self.ui_preferences:
            self.ui_preferences = self.default_ui_preferences
            
        super().save(*args, **kwargs)
