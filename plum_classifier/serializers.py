from rest_framework import serializers
from .models import PlumBatch, PlumClassification, Notification, ModelVersion
from users.serializers import UserSerializer, FarmSerializer

class PlumClassificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle PlumClassification.
    """
    uploaded_by_details = UserSerializer(source='uploaded_by', read_only=True)
    farm_details = FarmSerializer(source='farm', read_only=True)
    class_name_display = serializers.CharField(source='get_class_name_display', read_only=True)
    
    class Meta:
        model = PlumClassification
        fields = ('id', 'image_path', 'original_filename', 'uploaded_by', 'uploaded_by_details',
                  'farm', 'farm_details', 'batch', 'classification_result', 'class_name',
                  'class_name_display', 'confidence_score', 'is_plum', 'processing_time',
                  'device_info', 'geo_location', 'created_at')
        read_only_fields = ('id', 'uploaded_by', 'uploaded_by_details', 'created_at')
    
    def create(self, validated_data):
        """
        Crée une nouvelle classification en définissant l'utilisateur qui l'a téléchargée.
        """
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class PlumBatchSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle PlumBatch.
    """
    farm_details = FarmSerializer(source='farm', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    classifications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PlumBatch
        fields = ('id', 'name', 'description', 'farm', 'farm_details', 'created_by',
                  'created_by_details', 'status', 'status_display', 'classification_summary',
                  'total_plums', 'quality_distribution', 'classifications_count',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_by', 'created_by_details', 'classification_summary',
                           'total_plums', 'quality_distribution', 'created_at', 'updated_at')
    
    def get_classifications_count(self, obj):
        """
        Retourne le nombre de classifications dans ce lot.
        """
        return obj.classifications.count()
    
    def create(self, validated_data):
        """
        Crée un nouveau lot en définissant l'utilisateur qui l'a créé.
        """
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Notification.
    """
    class Meta:
        model = Notification
        fields = ('id', 'user', 'title', 'message', 'type', 'is_read',
                  'content_type', 'object_id', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        """
        Crée une nouvelle notification en définissant l'utilisateur si non spécifié.
        """
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ModelVersionSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle ModelVersion.
    """
    class Meta:
        model = ModelVersion
        fields = ('id', 'name', 'version', 'file_path', 'metadata_path', 'model_type',
                  'num_classes', 'input_shape', 'confidence_threshold', 'accuracy',
                  'f1_score', 'precision', 'recall', 'training_date', 'training_duration',
                  'dataset_size', 'is_active', 'is_production', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
