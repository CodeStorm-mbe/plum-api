from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'preferences', views.DashboardPreferenceViewSet, basename='dashboard-preferences')
router.register(r'analytics', views.DashboardAnalyticsViewSet, basename='dashboard-analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('user/', views.DashboardViewSet.as_view({'get': 'user_dashboard'}), name='user-dashboard'),
    path('admin/', views.DashboardViewSet.as_view({'get': 'admin_dashboard'}), name='admin-dashboard'),
    path('technician/', views.DashboardViewSet.as_view({'get': 'technician_dashboard'}), name='technician-dashboard'),
    path('farmer/', views.DashboardViewSet.as_view({'get': 'farmer_dashboard'}), name='farmer-dashboard'),
]
