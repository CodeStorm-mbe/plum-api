from rest_framework import serializers
from .models import DashboardMetric, DashboardPreference
from plum_classifier.serializers import PlumClassificationSerializer

class DashboardMetricSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle DashboardMetric.
    """
    class Meta:
        model = DashboardMetric
        fields = '__all__'


class DashboardPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle DashboardPreference.
    """
    class Meta:
        model = DashboardPreference
        fields = ('id', 'layout', 'visible_metrics', 'refresh_interval', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class AdminDashboardSerializer(serializers.Serializer):
    """
    Serializer pour les données du dashboard administrateur.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = PlumClassificationSerializer(many=True)
    total_users = serializers.IntegerField()
    users_by_role = serializers.DictField(child=serializers.IntegerField())
    active_users = serializers.IntegerField()
    system_performance = serializers.DictField()


class TechnicianDashboardSerializer(serializers.Serializer):
    """
    Serializer pour les données du dashboard technicien.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = PlumClassificationSerializer(many=True)
    managed_farms = serializers.IntegerField()
    farm_performance = serializers.ListField(child=serializers.DictField())
    quality_trends = serializers.ListField(child=serializers.DictField())


class FarmerDashboardSerializer(serializers.Serializer):
    """
    Serializer pour les données du dashboard agriculteur.
    """
    total_classifications = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    class_distribution = serializers.DictField(child=serializers.IntegerField())
    class_percentages = serializers.DictField(child=serializers.FloatField())
    recent_classifications = PlumClassificationSerializer(many=True)
    farms = serializers.ListField(child=serializers.DictField())
    total_batches = serializers.IntegerField()
    pending_batches = serializers.IntegerField()


class TimeSeriesDataSerializer(serializers.Serializer):
    """
    Serializer pour les données de séries temporelles.
    """
    date = serializers.DateTimeField()
    value = serializers.FloatField()


class QualityTrendSerializer(serializers.Serializer):
    """
    Serializer pour les tendances de qualité.
    """
    category = serializers.CharField()
    data = serializers.ListField(child=serializers.DictField())


class FarmComparisonSerializer(serializers.Serializer):
    """
    Serializer pour la comparaison des fermes.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    location = serializers.CharField()
    total_classifications = serializers.IntegerField()
    quality_score = serializers.FloatField()
    efficiency = serializers.FloatField()
    volume = serializers.IntegerField()


class QualityPredictionSerializer(serializers.Serializer):
    """
    Serializer pour les prédictions de qualité.
    """
    prediction_date = serializers.DateTimeField()
    predicted_distribution = serializers.DictField(child=serializers.FloatField())
    confidence = serializers.FloatField()
    method = serializers.CharField()


class ActivityHeatmapSerializer(serializers.Serializer):
    """
    Serializer pour le heatmap d'activité.
    """
    data = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))
    days = serializers.ListField(child=serializers.CharField())
    hours = serializers.ListField(child=serializers.CharField())
    max_value = serializers.IntegerField()


class ClassificationAccuracySerializer(serializers.Serializer):
    """
    Serializer pour les métriques d'exactitude de classification.
    """
    average_confidence = serializers.FloatField()
    confidence_by_class = serializers.DictField(child=serializers.FloatField())
    confidence_distribution = serializers.DictField(child=serializers.IntegerField())
    total_classifications = serializers.IntegerField()
