from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DashboardViewSet, DashboardPreferenceViewSet

# Créer un routeur pour les ViewSets
router = DefaultRouter()
router.register(r'preferences', DashboardPreferenceViewSet, basename='dashboard-preference')

urlpatterns = [
    # Inclure les routes générées automatiquement
    path('', include(router.urls)),
    
    # Routes spécifiques pour les dashboards
    path('user/', DashboardViewSet.as_view({'get': 'user_dashboard'}), name='user-dashboard'),
    path('admin/', DashboardViewSet.as_view({'get': 'admin_dashboard'}), name='admin-dashboard'),
    path('technician/', DashboardViewSet.as_view({'get': 'technician_dashboard'}), name='technician-dashboard'),
    path('farmer/', DashboardViewSet.as_view({'get': 'farmer_dashboard'}), name='farmer-dashboard'),
]
