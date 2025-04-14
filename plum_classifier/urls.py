from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    PlumClassificationViewSet,
    PlumBatchViewSet,
    ModelVersionViewSet
)

# Configuration de Swagger/OpenAPI
schema_view = get_schema_view(
   openapi.Info(
      title="API de Classification des Prunes",
      default_version='v1',
      description="API pour la classification automatique des prunes destinée aux agriculteurs",
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'classifications', PlumClassificationViewSet, basename='classification')
router.register(r'batches', PlumBatchViewSet, basename='batch')
router.register(r'models', ModelVersionViewSet, basename='model')

urlpatterns = [
    # Inclure les routes générées automatiquement
    path('', include(router.urls)),
    
    # Documentation Swagger/OpenAPI
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
