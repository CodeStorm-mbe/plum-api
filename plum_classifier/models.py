from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User, Farm

class PlumBatch(models.Model):
    """
    Modèle représentant un lot de prunes à classifier.
    """
    STATUS_CHOICES = (
        ('pending', _('En attente')),
        ('classified', _('Classifié')),
        ('archived', _('Archivé')),
    )
    
    name = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'), blank=True, null=True)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='batches', verbose_name=_('ferme'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_batches', verbose_name=_('créé par'))
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Résumé de classification
    classification_summary = models.JSONField(_('résumé de classification'), default=dict, blank=True)
    total_plums = models.PositiveIntegerField(_('nombre total de prunes'), default=0)
    quality_distribution = models.JSONField(_('distribution de qualité'), default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('lot de prunes')
        verbose_name_plural = _('lots de prunes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.farm.name}"
    
    def update_classification_summary(self):
        """
        Met à jour le résumé de classification basé sur les classifications individuelles.
        """
        classifications = self.classifications.all()
        self.total_plums = classifications.count()
        
        # Calculer la distribution de qualité
        quality_counts = {}
        for classification in classifications:
            class_name = classification.class_name
            quality_counts[class_name] = quality_counts.get(class_name, 0) + 1
        
        # Calculer les pourcentages
        quality_distribution = {}
        for class_name, count in quality_counts.items():
            percentage = (count / self.total_plums) * 100 if self.total_plums > 0 else 0
            quality_distribution[class_name] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        self.quality_distribution = quality_distribution
        
        # Mettre à jour le résumé global
        self.classification_summary = {
            'total_plums': self.total_plums,
            'quality_distribution': quality_distribution,
            'average_confidence': self.get_average_confidence(),
            'last_updated': self.updated_at.isoformat() if self.updated_at else None
        }
        
        # Mettre à jour le statut si nécessaire
        if self.total_plums > 0 and self.status == 'pending':
            self.status = 'classified'
        
        self.save()
    
    def get_average_confidence(self):
        """
        Calcule la confiance moyenne pour toutes les classifications de ce lot.
        """
        classifications = self.classifications.all()
        if not classifications:
            return 0
        
        total_confidence = sum(c.confidence_score for c in classifications)
        return round(total_confidence / classifications.count(), 4)


class PlumClassification(models.Model):
    """
    Modèle représentant une classification individuelle de prune.
    """
    CLASS_CHOICES = (
        ('bonne_qualite', _('Bonne qualité')),
        ('non_mure', _('Non mûre')),
        ('tachetee', _('Tachetée')),
        ('fissuree', _('Fissurée')),
        ('meurtrie', _('Meurtrie')),
        ('pourrie', _('Pourrie')),
    )
    
    # Informations sur l'image
    image_path = models.CharField(_('chemin de l\'image'), max_length=255)
    original_filename = models.CharField(_('nom de fichier original'), max_length=255, blank=True, null=True)
    
    # Relations
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classifications', verbose_name=_('téléchargé par'))
    farm = models.ForeignKey(Farm, on_delete=models.SET_NULL, related_name='classifications', null=True, blank=True, verbose_name=_('ferme'))
    batch = models.ForeignKey(PlumBatch, on_delete=models.SET_NULL, related_name='classifications', null=True, blank=True, verbose_name=_('lot'))
    
    # Résultats de classification
    classification_result = models.JSONField(_('résultat de classification'), default=dict)
    class_name = models.CharField(_('classe'), max_length=20, choices=CLASS_CHOICES)
    confidence_score = models.FloatField(_('score de confiance'))
    is_plum = models.BooleanField(_('est une prune'), default=True)
    
    # Métadonnées
    processing_time = models.FloatField(_('temps de traitement (s)'), blank=True, null=True)
    device_info = models.TextField(_('informations sur l\'appareil'), blank=True, null=True)
    geo_location = models.JSONField(_('localisation géographique'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('classification de prune')
        verbose_name_plural = _('classifications de prunes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_class_name_display()} ({self.confidence_score:.2f})"
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour mettre à jour le résumé du lot après sauvegarde.
        """
        super().save(*args, **kwargs)
        
        # Mettre à jour le résumé du lot si applicable
        if self.batch:
            self.batch.update_classification_summary()


class Notification(models.Model):
    """
    Modèle pour les notifications utilisateur.
    """
    TYPE_CHOICES = (
        ('info', _('Information')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('success', _('Succès')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name=_('utilisateur'))
    title = models.CharField(_('titre'), max_length=100)
    message = models.TextField(_('message'))
    type = models.CharField(_('type'), max_length=10, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(_('lu'), default=False)
    
    # Champs polymorphiques pour lier la notification à différents types d'objets
    content_type = models.CharField(_('type de contenu'), max_length=50, blank=True, null=True)
    object_id = models.PositiveIntegerField(_('ID de l\'objet'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ModelVersion(models.Model):
    """
    Modèle pour suivre les versions du modèle de classification.
    """
    name = models.CharField(_('nom'), max_length=100)
    version = models.CharField(_('version'), max_length=20)
    file_path = models.CharField(_('chemin du fichier'), max_length=255)
    metadata_path = models.CharField(_('chemin des métadonnées'), max_length=255, blank=True, null=True)
    
    # Paramètres du modèle
    model_type = models.CharField(_('type de modèle'), max_length=50)
    num_classes = models.PositiveIntegerField(_('nombre de classes'))
    input_shape = models.JSONField(_('forme d\'entrée'), default=list)
    confidence_threshold = models.FloatField(_('seuil de confiance'), default=0.7)
    
    # Métriques de performance
    accuracy = models.FloatField(_('précision'), blank=True, null=True)
    f1_score = models.FloatField(_('score F1'), blank=True, null=True)
    precision = models.FloatField(_('précision'), blank=True, null=True)
    recall = models.FloatField(_('rappel'), blank=True, null=True)
    
    # Informations sur l'entraînement
    training_date = models.DateTimeField(_('date d\'entraînement'), blank=True, null=True)
    training_duration = models.FloatField(_('durée d\'entraînement (h)'), blank=True, null=True)
    dataset_size = models.PositiveIntegerField(_('taille du jeu de données'), blank=True, null=True)
    
    # État du modèle
    is_active = models.BooleanField(_('actif'), default=False)
    is_production = models.BooleanField(_('en production'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('version du modèle')
        verbose_name_plural = _('versions du modèle')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
