from django.urls import path, include
from rest_framework.routers import DefaultRouter

from plum_classifier.views import (
    PlumClassificationViewSet,
    PlumBatchViewSet,
    ModelVersionViewSet
)
from users.views import UserViewSet, FarmViewSet

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'classifications', PlumClassificationViewSet, basename='classification')
router.register(r'batches', PlumBatchViewSet, basename='batch')
router.register(r'models', ModelVersionViewSet, basename='model')

# Documentation Swagger/OpenAPI est configurée dans plum_project.urls

urlpatterns = [
    # Inclure les routes générées automatiquement
    path('', include(router.urls)),
    
    # Inclure les routes d'authentification
    path('auth/', include('authentication.urls')),
    
    # Inclure les routes spécifiques au classificateur de prunes
    path('plum-classifier/', include('plum_classifier.urls')),
    path('users/' ,include('users.urls'))
]
