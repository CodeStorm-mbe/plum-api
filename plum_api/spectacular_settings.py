"""
Configuration de la documentation de l'API avec drf-spectacular.
"""

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

# Configuration de drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'API de Classification de Prunes',
    'DESCRIPTION': 'API pour la classification de prunes utilisant un modèle d\'IA basé sur EfficientNet',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentication', 'description': 'Endpoints d\'authentification'},
        {'name': 'Users', 'description': 'Gestion des utilisateurs'},
        {'name': 'Plum Classification', 'description': 'Classification des prunes'},
        {'name': 'Batch Processing', 'description': 'Traitement par lot'},
        {'name': 'Notifications', 'description': 'Gestion des notifications'},
        {'name': 'Dashboard', 'description': 'Statistiques et tableau de bord'},
        {'name': 'API Management', 'description': 'Gestion des clés API et logs'},
        {'name': 'Feedback', 'description': 'Retours sur les classifications'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
    },
}
