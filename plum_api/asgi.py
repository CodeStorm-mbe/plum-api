"""
Configuration ASGI pour le projet plum_api.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Définir la variable d'environnement pour les paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plum_api.settings')

# Importer le routage des WebSockets (sera créé plus tard)
import api.routing

# Configurer l'application ASGI
application = ProtocolTypeRouter({
    # Django gère les requêtes HTTP standard
    "http": get_asgi_application(),
    
    # WebSocket avec authentification et validation d'origine
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                api.routing.websocket_urlpatterns
            )
        )
    ),
})
