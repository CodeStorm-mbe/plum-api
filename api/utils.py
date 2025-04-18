"""
Module d'utilitaires pour améliorer la maintenabilité du code.
Fournit des décorateurs, mixins et fonctions utilitaires pour le projet.
"""

import logging
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

class ResponseBuilder:
    """
    Classe utilitaire pour construire des réponses API cohérentes.
    """
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """
        Construit une réponse de succès.
        
        Args:
            data: Les données à renvoyer
            message: Message de succès optionnel
            status_code: Code de statut HTTP
            
        Returns:
            Response: Objet Response de DRF
        """
        response_data = {
            'success': True,
            'data': data or {}
        }
        
        if message:
            response_data['message'] = message
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Construit une réponse d'erreur.
        
        Args:
            message: Message d'erreur
            errors: Détails des erreurs
            status_code: Code de statut HTTP
            
        Returns:
            Response: Objet Response de DRF
        """
        response_data = {
            'success': False,
            'message': message
        }
        
        if errors:
            response_data['errors'] = errors
            
        return Response(response_data, status=status_code)


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour DRF.
    
    Args:
        exc: L'exception levée
        context: Le contexte de la requête
        
    Returns:
        Response: Réponse formatée pour l'exception
    """
    # Appeler d'abord le gestionnaire d'exceptions par défaut
    response = exception_handler(exc, context)
    
    # Si le gestionnaire par défaut a retourné une réponse
    if response is not None:
        # Récupérer les détails de l'exception
        error_data = {}
        
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                for key, value in exc.detail.items():
                    if isinstance(value, list):
                        error_data[key] = value[0]
                    else:
                        error_data[key] = value
            elif isinstance(exc.detail, list):
                error_message = exc.detail[0] if exc.detail else _("Une erreur s'est produite.")
                return ResponseBuilder.error(
                    message=str(error_message),
                    status_code=response.status_code
                )
            else:
                error_message = exc.detail
                return ResponseBuilder.error(
                    message=str(error_message),
                    status_code=response.status_code
                )
        
        # Construire une réponse d'erreur formatée
        if error_data:
            return ResponseBuilder.error(
                message=_("Des erreurs de validation se sont produites."),
                errors=error_data,
                status_code=response.status_code
            )
        else:
            return ResponseBuilder.error(
                message=_("Une erreur s'est produite."),
                status_code=response.status_code
            )
    
    # Si le gestionnaire par défaut n'a pas retourné de réponse, logger l'exception
    logger.exception("Exception non gérée: %s", exc)
    
    # Retourner une réponse d'erreur générique
    return ResponseBuilder.error(
        message=_("Une erreur serveur s'est produite."),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def log_method_calls(level=logging.DEBUG):
    """
    Décorateur pour logger les appels de méthodes.
    
    Args:
        level: Niveau de logging
        
    Returns:
        Callable: Décorateur
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Récupérer le nom de la classe si c'est une méthode
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                method_name = f"{class_name}.{func.__name__}"
            else:
                method_name = func.__name__
            
            # Logger l'appel de méthode
            logger.log(level, f"Appel de {method_name}")
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Logger la fin de l'exécution
            logger.log(level, f"Fin de {method_name}")
            
            return result
        return wrapper
    return decorator


class AuditMixin:
    """
    Mixin pour ajouter des fonctionnalités d'audit aux modèles.
    """
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour ajouter des informations d'audit.
        """
        # Vérifier si c'est une création ou une mise à jour
        is_new = self.pk is None
        
        # Ajouter des informations d'audit si les champs existent
        if hasattr(self, 'updated_at'):
            from django.utils import timezone
            self.updated_at = timezone.now()
        
        # Appeler la méthode save parent
        super().save(*args, **kwargs)
        
        # Logger l'opération
        model_name = self.__class__.__name__
        if is_new:
            logger.info(f"Création de {model_name} (ID: {self.pk})")
        else:
            logger.info(f"Mise à jour de {model_name} (ID: {self.pk})")


class ServiceBase:
    """
    Classe de base pour les services métier.
    Facilite la séparation de la logique métier des vues.
    """
    
    @classmethod
    def execute(cls, **kwargs):
        """
        Exécute le service et retourne le résultat.
        
        Args:
            **kwargs: Arguments pour le service
            
        Returns:
            Any: Résultat du service
        """
        instance = cls(**kwargs)
        return instance.process()
    
    def __init__(self, **kwargs):
        """
        Initialise le service avec les arguments fournis.
        
        Args:
            **kwargs: Arguments pour le service
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def process(self):
        """
        Méthode principale à implémenter dans les classes dérivées.
        
        Returns:
            Any: Résultat du service
        """
        raise NotImplementedError("La méthode process() doit être implémentée dans les classes dérivées.")


def validate_required_fields(data, required_fields):
    """
    Valide la présence des champs requis dans les données.
    
    Args:
        data: Dictionnaire de données
        required_fields: Liste des champs requis
        
    Returns:
        tuple: (is_valid, errors)
    """
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors[field] = _("Ce champ est obligatoire.")
    
    return len(errors) == 0, errors
