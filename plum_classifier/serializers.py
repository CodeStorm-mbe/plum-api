"""
Sérialiseurs pour l'application plum_classifier.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PlumImage, ClassificationResult, BatchClassificationJob, ModelMetrics

User = get_user_model()


class PlumImageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle PlumImage.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PlumImage
        fields = [
            'id', 'user', 'user_email', 'image', 'image_url', 'uploaded_at',
            'location', 'notes', 'ground_truth'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'uploaded_at']
    
    def get_image_url(self, obj):
        """
        Récupère l'URL de l'image.
        """
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url') and request:
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def create(self, validated_data):
        """
        Crée une nouvelle instance de PlumImage avec l'utilisateur actuel.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ClassificationResultSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle ClassificationResult.
    """
    plum_image_url = serializers.SerializerMethodField()
    probabilities = serializers.SerializerMethodField()
    
    class Meta:
        model = ClassificationResult
        fields = [
            'id', 'plum_image', 'plum_image_url', 'predicted_class', 'confidence',
            'is_plum', 'probabilities', 'classified_at', 'model_version', 'processing_time'
        ]
        read_only_fields = ['id', 'plum_image', 'plum_image_url', 'predicted_class', 'confidence',
                           'is_plum', 'probabilities', 'classified_at', 'model_version', 'processing_time']
    
    def get_plum_image_url(self, obj):
        """
        Récupère l'URL de l'image de prune.
        """
        request = self.context.get('request')
        if obj.plum_image and obj.plum_image.image and hasattr(obj.plum_image.image, 'url') and request:
            return request.build_absolute_uri(obj.plum_image.image.url)
        return None
    
    def get_probabilities(self, obj):
        """
        Récupère les probabilités pour chaque classe.
        """
        return {
            'bonne_qualite': obj.prob_bonne_qualite,
            'non_mure': obj.prob_non_mure,
            'tachetee': obj.prob_tachetee,
            'fissuree': obj.prob_fissuree,
            'meurtrie': obj.prob_meurtrie,
            'pourrie': obj.prob_pourrie
        }


class BatchClassificationJobSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle BatchClassificationJob.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = BatchClassificationJob
        fields = [
            'id', 'user', 'user_email', 'created_at', 'updated_at', 'status',
            'total_images', 'processed_images', 'success_count', 'error_count',
            'report_file', 'progress_percentage'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'updated_at',
                           'status', 'total_images', 'processed_images', 'success_count',
                           'error_count', 'report_file', 'progress_percentage']
    
    def create(self, validated_data):
        """
        Crée une nouvelle instance de BatchClassificationJob avec l'utilisateur actuel.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ModelMetricsSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle ModelMetrics.
    """
    class Meta:
        model = ModelMetrics
        fields = [
            'id', 'model_version', 'deployed_at', 'accuracy', 'precision',
            'recall', 'f1_score', 'class_metrics', 'confusion_matrix',
            'total_predictions', 'avg_confidence', 'avg_processing_time'
        ]
        read_only_fields = ['id', 'model_version', 'deployed_at', 'accuracy',
                           'precision', 'recall', 'f1_score', 'class_metrics',
                           'confusion_matrix', 'total_predictions', 'avg_confidence',
                           'avg_processing_time']


class ClassifyImageSerializer(serializers.Serializer):
    """
    Sérialiseur pour la classification d'une image.
    """
    image = serializers.ImageField(required=True)
    location = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    ground_truth = serializers.ChoiceField(
        choices=PlumImage.CATEGORY_CHOICES,
        required=False,
        allow_blank=True
    )
    save_result = serializers.BooleanField(default=True)
    send_realtime = serializers.BooleanField(default=True)


class BatchClassifySerializer(serializers.Serializer):
    """
    Sérialiseur pour la classification par lot.
    """
    image_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    all_unclassified = serializers.BooleanField(default=False)
