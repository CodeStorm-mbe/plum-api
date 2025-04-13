from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé qui étend le gestionnaire par défaut de DRF.
    """
    # Appel du gestionnaire d'exceptions par défaut de DRF
    response = drf_exception_handler(exc, context)
    
    # Si le gestionnaire par défaut a retourné une réponse, on la retourne
    if response is not None:
        return response
    
    # Gestion des exceptions non gérées par le gestionnaire par défaut
    return Response(
        {"detail": str(exc)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )