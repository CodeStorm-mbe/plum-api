from django.urls import path

from .views import (
    UserList, UserDetail, UserProfile, UserSettingsView, user_stats,
    FarmList, FarmDetail, farm_stats, farm_batches, farms_nearby
)

app_name = 'users'

urlpatterns = [
    # Routes utilisateurs
    path('users/', UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user-detail'),
    path('users/me/', UserProfile.as_view(), name='user-profile'),
    path('users/settings/', UserSettingsView.as_view(), name='user-settings'),
    path('users/stats/', user_stats, name='user-stats'),
    
    # Routes fermes
    path('farms/', FarmList.as_view(), name='farm-list'),
    path('farms/<int:pk>/', FarmDetail.as_view(), name='farm-detail'),
    path('farms/<int:pk>/stats/', farm_stats, name='farm-stats'),
    path('farms/<int:pk>/batches/', farm_batches, name='farm-batches'),
    path('farms/nearby/', farms_nearby, name='farms-nearby'),
]
