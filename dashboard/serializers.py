from rest_framework import serializers
from .models import DashboardMetric, DashboardPreference
from users.models import User, Farm
from plum_classifier.models import PlumClassification, PlumBatch, ModelVersion

class DashboardMetricSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les métriques du dashboard.
    """
    class Meta:
        model = DashboardMetric
        fields = '__all__'


class DashboardPreferenceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les préférences de dashboard des utilisateurs.
    """
    class Meta:
        model = DashboardPreference
        fields = '__all__'


class AdminDashboardSerializer(serializers.Serializer):
    """
    Sérialiseur pour le dashboard administrateur.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = serializers.ListField(child=serializers.DictField())
    total_users = serializers.IntegerField()
    users_by_role = serializers.DictField(child=serializers.IntegerField())
    active_users = serializers.IntegerField()
    system_performance = serializers.DictField()


class TechnicianDashboardSerializer(serializers.Serializer):
    """
    Sérialiseur pour le dashboard technicien.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = serializers.ListField(child=serializers.DictField())
    managed_farms = serializers.IntegerField()
    farm_performance = serializers.ListField(child=serializers.DictField())
    quality_trends = serializers.ListField(child=serializers.DictField())


class FarmerDashboardSerializer(serializers.Serializer):
    """
    Sérialiseur pour le dashboard agriculteur.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = serializers.ListField(child=serializers.DictField())
    farms = serializers.ListField(child=serializers.DictField())
    total_batches = serializers.IntegerField()
    pending_batches = serializers.IntegerField()
