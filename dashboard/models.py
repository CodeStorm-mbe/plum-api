from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from users.models import Farm
from plum_classifier.models import PlumBatch, PlumClassification

class DashboardMetric(models.Model):
    """
    Modèle pour stocker les métriques du dashboard.
    """
    name = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    value = models.JSONField(_('valeur'), default=dict)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboard_metrics',
        verbose_name=_('utilisateur'),
        null=True,
        blank=True
    )
    farm = models.ForeignKey(
        Farm, 
        on_delete=models.CASCADE, 
        related_name='dashboard_metrics',
        verbose_name=_('ferme'),
        null=True,
        blank=True
    )
    
    # Métadonnées
    metric_type = models.CharField(_('type de métrique'), max_length=50)
    time_period = models.CharField(_('période'), max_length=20, default='all')
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('métrique de dashboard')
        verbose_name_plural = _('métriques de dashboard')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['farm']),
            models.Index(fields=['metric_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.metric_type})"


class DashboardPreference(models.Model):
    """
    Modèle pour stocker les préférences de dashboard des utilisateurs.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='dashboard_preferences',
        verbose_name=_('utilisateur')
    )
    layout = models.JSONField(_('disposition'), default=dict)
    visible_metrics = models.JSONField(_('métriques visibles'), default=list)
    refresh_interval = models.PositiveIntegerField(_('intervalle de rafraîchissement (s)'), default=300)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('préférence de dashboard')
        verbose_name_plural = _('préférences de dashboard')
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Préférences de dashboard de {self.user.username}"
    
    @property
    def default_layout(self):
        """Retourne la disposition par défaut selon le rôle de l'utilisateur."""
        role = self.user.role
        
        if role == 'admin':
            return {
                'columns': 3,
                'widgets': [
                    {'id': 'user_stats', 'position': 0, 'size': 'medium'},
                    {'id': 'system_performance', 'position': 1, 'size': 'medium'},
                    {'id': 'classification_distribution', 'position': 2, 'size': 'medium'},
                    {'id': 'recent_activity', 'position': 3, 'size': 'large'},
                ]
            }
        elif role == 'technician':
            return {
                'columns': 2,
                'widgets': [
                    {'id': 'farm_performance', 'position': 0, 'size': 'large'},
                    {'id': 'quality_trends', 'position': 1, 'size': 'medium'},
                    {'id': 'classification_distribution', 'position': 2, 'size': 'medium'},
                    {'id': 'recent_activity', 'position': 3, 'size': 'large'},
                ]
            }
        else:  # farmer
            return {
                'columns': 2,
                'widgets': [
                    {'id': 'farm_summary', 'position': 0, 'size': 'medium'},
                    {'id': 'batch_status', 'position': 1, 'size': 'medium'},
                    {'id': 'classification_distribution', 'position': 2, 'size': 'medium'},
                    {'id': 'recent_activity', 'position': 3, 'size': 'large'},
                ]
            }
    
    @property
    def default_visible_metrics(self):
        """Retourne les métriques visibles par défaut selon le rôle de l'utilisateur."""
        role = self.user.role
        
        base_metrics = [
            'total_classifications',
            'average_confidence',
            'class_distribution',
        ]
        
        if role == 'admin':
            return base_metrics + [
                'total_users',
                'users_by_role',
                'active_users',
                'system_performance',
            ]
        elif role == 'technician':
            return base_metrics + [
                'managed_farms',
                'farm_performance',
                'quality_trends',
            ]
        else:  # farmer
            return base_metrics + [
                'farms',
                'total_batches',
                'pending_batches',
            ]
    
    def save(self, *args, **kwargs):
        """Assure que les préférences par défaut sont définies."""
        if not self.layout:
            self.layout = self.default_layout
        
        if not self.visible_metrics:
            self.visible_metrics = self.default_visible_metrics
            
        super().save(*args, **kwargs)
