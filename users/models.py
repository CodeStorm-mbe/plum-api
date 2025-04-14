"""
Modèles de données pour l'application users.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée et enregistre un utilisateur avec l'email et le mot de passe donnés.
        """
        if not email:
            raise ValueError(_('L\'adresse email est obligatoire'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée et enregistre un superutilisateur avec l'email et le mot de passe donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', User.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec UUID comme identifiant et gestion des rôles.
    """
    # Rôles disponibles
    ADMIN = 'admin'
    AGRICULTEUR = 'agriculteur'
    TECHNICIEN = 'technicien'
    CONSULTANT = 'consultant'
    
    ROLE_CHOICES = [
        (ADMIN, _('Administrateur')),
        (AGRICULTEUR, _('Agriculteur')),
        (TECHNICIEN, _('Technicien')),
        (CONSULTANT, _('Consultant')),
    ]
    
    # Remplacer l'ID par un UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Remplacer le nom d'utilisateur par l'email
    username = None
    email = models.EmailField(_('adresse email'), unique=True)
    
    # Champs supplémentaires
    role = models.CharField(_('rôle'), max_length=20, choices=ROLE_CHOICES, default=AGRICULTEUR)
    phone_number = models.CharField(_('numéro de téléphone'), max_length=20, blank=True, null=True)
    address = models.TextField(_('adresse'), blank=True, null=True)
    profile_picture = models.ImageField(_('photo de profil'), upload_to='profile_pictures/', blank=True, null=True)
    
    # Champs pour la vérification de l'email
    email_verified = models.BooleanField(_('email vérifié'), default=False)
    
    # Préférences de notification
    notification_email = models.BooleanField(_('notifications par email'), default=True)
    notification_classification = models.BooleanField(_('notifications de classification'), default=True)
    notification_reports = models.BooleanField(_('notifications de rapports'), default=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    
    # Spécifier les champs requis
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    # Utiliser le gestionnaire personnalisé
    objects = UserManager()
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Retourne le prénom et le nom avec un espace au milieu.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """
        Retourne le prénom de l'utilisateur.
        """
        return self.first_name
    
    @property
    def is_admin(self):
        """
        Vérifie si l'utilisateur est un administrateur.
        """
        return self.role == self.ADMIN
    
    @property
    def is_agriculteur(self):
        """
        Vérifie si l'utilisateur est un agriculteur.
        """
        return self.role == self.AGRICULTEUR
    
    @property
    def is_technicien(self):
        """
        Vérifie si l'utilisateur est un technicien.
        """
        return self.role == self.TECHNICIEN
    
    @property
    def is_consultant(self):
        """
        Vérifie si l'utilisateur est un consultant.
        """
        return self.role == self.CONSULTANT


class EmailVerificationToken(models.Model):
    """
    Modèle pour stocker les tokens de vérification d'email.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.UUIDField(_('token'), default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    expires_at = models.DateTimeField(_('date d\'expiration'))
    is_used = models.BooleanField(_('utilisé'), default=False)
    
    class Meta:
        verbose_name = _('token de vérification d\'email')
        verbose_name_plural = _('tokens de vérification d\'email')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token pour {self.user.email}"
    
    @property
    def is_expired(self):
        """
        Vérifie si le token est expiré.
        """
        from django.utils import timezone
        return self.expires_at < timezone.now()


class PasswordResetToken(models.Model):
    """
    Modèle pour stocker les tokens de réinitialisation de mot de passe.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_tokens')
    token = models.UUIDField(_('token'), default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    expires_at = models.DateTimeField(_('date d\'expiration'))
    is_used = models.BooleanField(_('utilisé'), default=False)
    
    class Meta:
        verbose_name = _('token de réinitialisation de mot de passe')
        verbose_name_plural = _('tokens de réinitialisation de mot de passe')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token pour {self.user.email}"
    
    @property
    def is_expired(self):
        """
        Vérifie si le token est expiré.
        """
        from django.utils import timezone
        return self.expires_at < timezone.now()
