"""
Modèles de données pour l'application plum_classifier.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import User


class PlumImage(models.Model):
    """
    Modèle pour stocker les images de prunes.
    """
    # Catégories de prunes
    BONNE_QUALITE = 'bonne_qualite'
    NON_MURE = 'non_mure'
    TACHETEE = 'tachetee'
    FISSUREE = 'fissuree'
    MEURTRIE = 'meurtrie'
    POURRIE = 'pourrie'
    
    CATEGORY_CHOICES = [
        (BONNE_QUALITE, _('Bonne qualité')),
        (NON_MURE, _('Non mûre')),
        (TACHETEE, _('Tachetée')),
        (FISSUREE, _('Fissurée')),
        (MEURTRIE, _('Meurtrie')),
        (POURRIE, _('Pourrie')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plum_images')
    image = models.ImageField(_('image'), upload_to='plum_images/')
    uploaded_at = models.DateTimeField(_('date d\'upload'), auto_now_add=True)
    
    # Métadonnées optionnelles
    location = models.CharField(_('lieu'), max_length=255, blank=True, null=True)
    notes = models.TextField(_('notes'), blank=True, null=True)
    
    # Champs pour la vérité terrain (si connue)
    ground_truth = models.CharField(_('vérité terrain'), max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    
    class Meta:
        verbose_name = _('image de prune')
        verbose_name_plural = _('images de prunes')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Image {self.id} par {self.user.email}"


class ClassificationResult(models.Model):
    """
    Modèle pour stocker les résultats de classification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plum_image = models.ForeignKey(PlumImage, on_delete=models.CASCADE, related_name='classifications')
    
    # Résultat de la classification
    predicted_class = models.CharField(_('classe prédite'), max_length=20, choices=PlumImage.CATEGORY_CHOICES)
    confidence = models.FloatField(_('confiance'))
    is_plum = models.BooleanField(_('est une prune'), default=True)
    
    # Probabilités détaillées pour chaque classe
    prob_bonne_qualite = models.FloatField(_('probabilité bonne qualité'), default=0.0)
    prob_non_mure = models.FloatField(_('probabilité non mûre'), default=0.0)
    prob_tachetee = models.FloatField(_('probabilité tachetée'), default=0.0)
    prob_fissuree = models.FloatField(_('probabilité fissurée'), default=0.0)
    prob_meurtrie = models.FloatField(_('probabilité meurtrie'), default=0.0)
    prob_pourrie = models.FloatField(_('probabilité pourrie'), default=0.0)
    
    # Métadonnées
    classified_at = models.DateTimeField(_('date de classification'), auto_now_add=True)
    model_version = models.CharField(_('version du modèle'), max_length=50)
    processing_time = models.FloatField(_('temps de traitement (ms)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('résultat de classification')
        verbose_name_plural = _('résultats de classification')
        ordering = ['-classified_at']
    
    def __str__(self):
        return f"Classification de {self.plum_image.id} : {self.predicted_class} ({self.confidence:.2f})"


class BatchClassificationJob(models.Model):
    """
    Modèle pour stocker les tâches de classification par lot.
    """
    # Statuts possibles
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (PROCESSING, _('En cours')),
        (COMPLETED, _('Terminé')),
        (FAILED, _('Échoué')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='batch_jobs')
    
    # Métadonnées
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de mise à jour'), auto_now=True)
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Statistiques
    total_images = models.IntegerField(_('nombre total d\'images'), default=0)
    processed_images = models.IntegerField(_('nombre d\'images traitées'), default=0)
    success_count = models.IntegerField(_('nombre de succès'), default=0)
    error_count = models.IntegerField(_('nombre d\'erreurs'), default=0)
    
    # Résultats
    report_file = models.FileField(_('fichier de rapport'), upload_to='batch_reports/', null=True, blank=True)
    
    class Meta:
        verbose_name = _('tâche de classification par lot')
        verbose_name_plural = _('tâches de classification par lot')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tâche {self.id} ({self.status})"
    
    @property
    def progress_percentage(self):
        """
        Calcule le pourcentage de progression.
        """
        if self.total_images == 0:
            return 0
        return int((self.processed_images / self.total_images) * 100)


class ModelMetrics(models.Model):
    """
    Modèle pour stocker les métriques du modèle de classification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Informations sur le modèle
    model_version = models.CharField(_('version du modèle'), max_length=50, unique=True)
    deployed_at = models.DateTimeField(_('date de déploiement'), auto_now_add=True)
    
    # Métriques de performance
    accuracy = models.FloatField(_('précision'), null=True, blank=True)
    precision = models.FloatField(_('précision (precision)'), null=True, blank=True)
    recall = models.FloatField(_('rappel'), null=True, blank=True)
    f1_score = models.FloatField(_('score F1'), null=True, blank=True)
    
    # Métriques par classe (stockées en JSON)
    class_metrics = models.JSONField(_('métriques par classe'), null=True, blank=True)
    
    # Matrice de confusion (stockée en JSON)
    confusion_matrix = models.JSONField(_('matrice de confusion'), null=True, blank=True)
    
    # Statistiques d'utilisation
    total_predictions = models.IntegerField(_('nombre total de prédictions'), default=0)
    avg_confidence = models.FloatField(_('confiance moyenne'), null=True, blank=True)
    avg_processing_time = models.FloatField(_('temps de traitement moyen (ms)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('métriques du modèle')
        verbose_name_plural = _('métriques du modèle')
        ordering = ['-deployed_at']
    
    def __str__(self):
        return f"Métriques pour {self.model_version}"
