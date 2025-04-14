"""
Modèles de données pour l'application api.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class ApiKey(models.Model):
    """
    Modèle pour stocker les clés API des utilisateurs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key = models.UUIDField(_('clé API'), default=uuid.uuid4, unique=True)
    name = models.CharField(_('nom'), max_length=100)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Limites d'utilisation
    requests_limit = models.IntegerField(_('limite de requêtes'), default=1000)
    requests_count = models.IntegerField(_('nombre de requêtes'), default=0)
    
    # Permissions
    can_read = models.BooleanField(_('peut lire'), default=True)
    can_write = models.BooleanField(_('peut écrire'), default=False)
    can_delete = models.BooleanField(_('peut supprimer'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    expires_at = models.DateTimeField(_('date d\'expiration'), null=True, blank=True)
    last_used_at = models.DateTimeField(_('dernière utilisation'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('clé API')
        verbose_name_plural = _('clés API')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Clé API {self.name} pour {self.user.email}"
    
    @property
    def is_expired(self):
        """
        Vérifie si la clé API est expirée.
        """
        from django.utils import timezone
        if self.expires_at is None:
            return False
        return self.expires_at < timezone.now()
    
    @property
    def has_reached_limit(self):
        """
        Vérifie si la clé API a atteint sa limite de requêtes.
        """
        return self.requests_count >= self.requests_limit


class ApiLog(models.Model):
    """
    Modèle pour enregistrer les logs d'utilisation de l'API.
    """
    # Types de requêtes
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    
    METHOD_CHOICES = [
        (GET, 'GET'),
        (POST, 'POST'),
        (PUT, 'PUT'),
        (PATCH, 'PATCH'),
        (DELETE, 'DELETE'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='api_logs')
    api_key = models.ForeignKey(ApiKey, on_delete=models.SET_NULL, null=True, related_name='logs')
    
    # Informations sur la requête
    endpoint = models.CharField(_('endpoint'), max_length=255)
    method = models.CharField(_('méthode'), max_length=10, choices=METHOD_CHOICES)
    status_code = models.IntegerField(_('code de statut'))
    
    # Métadonnées
    timestamp = models.DateTimeField(_('horodatage'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), null=True, blank=True)
    
    # Détails de la requête et de la réponse
    request_data = models.JSONField(_('données de la requête'), null=True, blank=True)
    response_data = models.JSONField(_('données de la réponse'), null=True, blank=True)
    processing_time = models.FloatField(_('temps de traitement (ms)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('log API')
        verbose_name_plural = _('logs API')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.method} {self.endpoint} ({self.status_code}) - {self.timestamp}"


class Notification(models.Model):
    """
    Modèle pour stocker les notifications des utilisateurs.
    """
    # Types de notifications
    CLASSIFICATION = 'classification'
    BATCH_COMPLETE = 'batch_complete'
    ACCOUNT = 'account'
    SYSTEM = 'system'
    
    TYPE_CHOICES = [
        (CLASSIFICATION, _('Classification')),
        (BATCH_COMPLETE, _('Traitement par lot terminé')),
        (ACCOUNT, _('Compte')),
        (SYSTEM, _('Système')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Contenu de la notification
    type = models.CharField(_('type'), max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(_('titre'), max_length=255)
    message = models.TextField(_('message'))
    
    # Statut de la notification
    is_read = models.BooleanField(_('lue'), default=False)
    is_sent_by_email = models.BooleanField(_('envoyée par email'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    read_at = models.DateTimeField(_('date de lecture'), null=True, blank=True)
    
    # Données supplémentaires (liens, actions, etc.)
    data = models.JSONField(_('données'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification {self.type} pour {self.user.email}: {self.title}"
    
    def mark_as_read(self):
        """
        Marque la notification comme lue.
        """
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class Feedback(models.Model):
    """
    Modèle pour stocker les retours des utilisateurs sur les classifications.
    """
    # Types de feedback
    CORRECT = 'correct'
    INCORRECT = 'incorrect'
    UNSURE = 'unsure'
    
    FEEDBACK_CHOICES = [
        (CORRECT, _('Correct')),
        (INCORRECT, _('Incorrect')),
        (UNSURE, _('Incertain')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    classification = models.ForeignKey('plum_classifier.ClassificationResult', on_delete=models.CASCADE, related_name='feedbacks')
    
    # Feedback
    feedback_type = models.CharField(_('type de feedback'), max_length=20, choices=FEEDBACK_CHOICES)
    correct_class = models.CharField(_('classe correcte'), max_length=20, null=True, blank=True)
    comment = models.TextField(_('commentaire'), blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('feedback')
        verbose_name_plural = _('feedbacks')
        ordering = ['-created_at']
        # Un utilisateur ne peut donner qu'un seul feedback par classification
        unique_together = ['user', 'classification']
    
    def __str__(self):
        return f"Feedback de {self.user.email} sur {self.classification.id}: {self.feedback_type}"
