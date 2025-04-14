from django.urls import path, include

from plum_classifier.views import (
    PlumClassificationViewSet,
    PlumBatchViewSet,
    ModelVersionViewSet
)

# Documentation Swagger/OpenAPI est configurée dans plum_project.urls

urlpatterns = [
    # Inclure les routes du classificateur de prunes
    path('classifications/', PlumClassificationViewSet.as_view({'get': 'list', 'post': 'create'}), name='classification-list'),
    path('classifications/<int:pk>/', PlumClassificationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='classification-detail'),
    
    path('batches/', PlumBatchViewSet.as_view({'get': 'list', 'post': 'create'}), name='batch-list'),
    path('batches/<int:pk>/', PlumBatchViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='batch-detail'),
    
    path('models/', ModelVersionViewSet.as_view({'get': 'list', 'post': 'create'}), name='model-list'),
    path('models/<int:pk>/', ModelVersionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='model-detail'),
    
    # Inclure les routes d'authentification
    path('auth/', include('authentication.urls')),
    
    # Inclure les routes spécifiques au classificateur de prunes
    path('plum-classifier/', include('plum_classifier.urls')),
    
    # Inclure les routes utilisateurs
    path('', include('users.urls')),
]
