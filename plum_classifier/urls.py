"""
Configuration des URLs pour l'application plum_classifier.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PlumImageViewSet,
    ClassificationResultViewSet,
    BatchClassificationJobViewSet,
    ModelMetricsViewSet
)

app_name = 'plum_classifier'

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'images', PlumImageViewSet, basename='plum_image')
router.register(r'classifications', ClassificationResultViewSet, basename='classification_result')
router.register(r'batch-jobs', BatchClassificationJobViewSet, basename='batch_job')
router.register(r'model-metrics', ModelMetricsViewSet, basename='model_metrics')

urlpatterns = [
    path('', include(router.urls)),
]
