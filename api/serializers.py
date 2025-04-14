"""
Sérialiseurs pour l'application api.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ApiKey, ApiLog, Notification, Feedback

User = get_user_model()


class ApiKeySerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle ApiKey.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ApiKey
        fields = [
            'id', 'user', 'user_email', 'key', 'name', 'is_active',
            'requests_limit', 'requests_count', 'can_read', 'can_write',
            'can_delete', 'created_at', 'expires_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'key', 'created_at', 'last_used_at']
    
    def create(self, validated_data):
        """
        Crée une nouvelle instance de ApiKey avec l'utilisateur actuel.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class ApiLogSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle ApiLog.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ApiLog
        fields = [
            'id', 'user', 'user_email', 'api_key', 'endpoint', 'method',
            'status_code', 'timestamp', 'ip_address', 'user_agent',
            'request_data', 'response_data', 'processing_time'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'api_key', 'endpoint',
                           'method', 'status_code', 'timestamp', 'ip_address',
                           'user_agent', 'request_data', 'response_data', 'processing_time']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Notification.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_email', 'type', 'title', 'message',
            'is_read', 'is_sent_by_email', 'created_at', 'read_at', 'data'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'read_at']
    
    def create(self, validated_data):
        """
        Crée une nouvelle instance de Notification avec l'utilisateur actuel.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class FeedbackSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Feedback.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'user_email', 'classification', 'feedback_type',
            'correct_class', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at']
    
    def create(self, validated_data):
        """
        Crée une nouvelle instance de Feedback avec l'utilisateur actuel.
        """
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class DashboardStatsSerializer(serializers.Serializer):
    """
    Sérialiseur pour les statistiques du tableau de bord.
    """
    total_images = serializers.IntegerField()
    total_classifications = serializers.IntegerField()
    recent_classifications = serializers.IntegerField()
    classification_distribution = serializers.DictField(child=serializers.IntegerField())
    avg_confidence = serializers.FloatField()
    user_stats = serializers.DictField(child=serializers.IntegerField(), required=False)
