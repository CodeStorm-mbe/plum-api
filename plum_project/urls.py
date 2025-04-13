from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Personnalisation du site d'administration
admin.site.site_header = "Administration du Système de Classification des Prunes"
admin.site.site_title = "Classification des Prunes"
admin.site.index_title = "Tableau de bord"

urlpatterns = [
    # Interface d'administration
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include('api.urls')),

    # Endpoint du schéma OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui-alt'),

    # ReDoc
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='schema-redoc'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
