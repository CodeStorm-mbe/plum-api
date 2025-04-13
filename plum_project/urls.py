from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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

# Personnalisation du site d'administration
admin.site.site_header = "Administration du Système de Classification des Prunes"
admin.site.site_title = "Classification des Prunes"
admin.site.index_title = "Tableau de bord"

urlpatterns = [
    # Interface d'administration
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Documentation Swagger/OpenAPI
    path("", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),  # Racine
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-alt'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
