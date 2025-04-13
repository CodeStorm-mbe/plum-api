from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, FarmViewSet

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'farms', FarmViewSet, basename='farm')

app_name = 'users'

urlpatterns = [
    # Inclure les routes générées automatiquement
    path('', include(router.urls)),
]
