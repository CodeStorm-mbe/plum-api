from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils.crypto import get_random_string

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds fields specific to the plum classification system.
    """
    ROLE_CHOICES = (
        ('farmer', _('Farmer')),
        ('technician', _('Technician')),
        ('admin', _('Administrator')),
    )
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='farmer')
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    profile_image = models.ImageField(_('profile image'), upload_to='profile_images/', blank=True, null=True)
    
    # Email verification
    email_verified = models.BooleanField(_('email verified'), default=False)
    email_verification_token = models.CharField(_('email verification token'), max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(_('email verification sent at'), blank=True, null=True)
    
    # Additional fields for farmers
    organization = models.CharField(_('organization'), max_length=100, blank=True, null=True)
    address = models.TextField(_('address'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Make email required
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.username
    
    @property
    def is_farmer(self):
        return self.role == 'farmer'
    
    @property
    def is_technician(self):
        return self.role == 'technician'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def generate_email_verification_token(self):
        """Generate a random token for email verification"""
        self.email_verification_token = get_random_string(64)
        return self.email_verification_token


class Farm(models.Model):
    """
    Farm model to represent a farm owned by a user.
    """
    name = models.CharField(_('name'), max_length=100)
    location = models.CharField(_('location'), max_length=255)
    size = models.DecimalField(_('size (hectares)'), max_digits=10, decimal_places=2, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    description = models.TextField(_('description'), blank=True, null=True)
    
    # Coordinates for map display
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('farm')
        verbose_name_plural = _('farms')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class UserSettings(models.Model):
    """
    User settings model to store user preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    notification_preferences = models.JSONField(_('notification preferences'), default=dict)
    ui_preferences = models.JSONField(_('UI preferences'), default=dict)
    language = models.CharField(_('language'), max_length=10, default='en')
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('user settings')
        verbose_name_plural = _('user settings')
    
    def __str__(self):
        return f"{self.user.username}'s settings"
