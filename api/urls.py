"""
Configuration des URLs pour l'application api.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ApiKeyViewSet,
    ApiLogViewSet,
    NotificationViewSet,
    FeedbackViewSet,
    DashboardViewSet
)

app_name = 'api'

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'api-keys', ApiKeyViewSet, basename='api_key')
router.register(r'api-logs', ApiLogViewSet, basename='api_log')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'feedbacks', FeedbackViewSet, basename='feedback')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
