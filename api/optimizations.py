"""
Module d'optimisation des performances pour les requêtes de base de données.
Fournit des fonctions et décorateurs pour améliorer les performances des requêtes.
"""

import time
import functools
import logging
from django.db import connection, reset_queries
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet, Prefetch

logger = logging.getLogger(__name__)

def query_debugger(func):
    """
    Décorateur pour analyser les performances des requêtes de base de données.
    Affiche le nombre de requêtes et le temps d'exécution.
    
    Usage:
        @query_debugger
        def ma_fonction(request):
            # Code utilisant des requêtes de base de données
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        if settings.DEBUG:
            query_count = len(connection.queries)
            query_time = sum(float(q['time']) for q in connection.queries)
            
            logger.debug(f"Fonction: {func.__name__}")
            logger.debug(f"Nombre de requêtes: {query_count}")
            logger.debug(f"Temps des requêtes: {query_time:.4f}s")
            logger.debug(f"Temps total: {end_time - start_time:.4f}s")
            
        return result
    return wrapper


def cached_queryset(timeout=3600, key_prefix=''):
    """
    Décorateur pour mettre en cache les résultats d'une fonction retournant un queryset.
    
    Args:
        timeout: Durée de vie du cache en secondes (par défaut: 1 heure)
        key_prefix: Préfixe pour la clé de cache
        
    Usage:
        @cached_queryset(timeout=300, key_prefix='dashboard')
        def get_recent_classifications(user_id):
            return PlumClassification.objects.filter(uploaded_by_id=user_id)[:10]
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Générer une clé de cache unique basée sur la fonction et ses arguments
            cache_key = f"{key_prefix}_{func.__name__}"
            for arg in args:
                cache_key += f"_{arg}"
            for key, value in kwargs.items():
                cache_key += f"_{key}_{value}"
            
            # Vérifier si le résultat est déjà en cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Résultat récupéré du cache: {cache_key}")
                return cached_result
            
            # Exécuter la fonction et mettre en cache le résultat
            result = func(*args, **kwargs)
            
            # Si le résultat est un QuerySet, l'évaluer avant de le mettre en cache
            if isinstance(result, QuerySet):
                result = list(result)
                
            cache.set(cache_key, result, timeout)
            logger.debug(f"Résultat mis en cache: {cache_key}")
            
            return result
        return wrapper
    return decorator


def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """
    Optimise un queryset en ajoutant select_related et prefetch_related.
    
    Args:
        queryset: Le queryset à optimiser
        select_related: Liste de champs pour select_related
        prefetch_related: Liste de champs ou objets Prefetch pour prefetch_related
        
    Returns:
        QuerySet: Le queryset optimisé
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
        
    if prefetch_related:
        # Convertir les chaînes simples en objets Prefetch si nécessaire
        prefetch_objects = []
        for item in prefetch_related:
            if isinstance(item, str):
                prefetch_objects.append(item)
            else:
                prefetch_objects.append(item)  # Supposé être un objet Prefetch
                
        queryset = queryset.prefetch_related(*prefetch_objects)
        
    return queryset


def batch_process(queryset, batch_size=1000, callback=None):
    """
    Traite un grand queryset par lots pour éviter les problèmes de mémoire.
    
    Args:
        queryset: Le queryset à traiter
        batch_size: Taille de chaque lot
        callback: Fonction à appeler pour chaque lot
        
    Returns:
        int: Nombre total d'objets traités
    """
    total_processed = 0
    
    # Récupérer l'ID du premier objet
    first_obj = queryset.order_by('id').first()
    if not first_obj:
        return 0
    
    current_id = first_obj.id - 1
    
    while True:
        # Récupérer le prochain lot
        batch = queryset.filter(id__gt=current_id).order_by('id')[:batch_size]
        batch_list = list(batch)
        
        if not batch_list:
            break
            
        # Mettre à jour l'ID pour le prochain lot
        current_id = batch_list[-1].id
        
        # Traiter le lot
        if callback:
            callback(batch_list)
            
        total_processed += len(batch_list)
        
    return total_processed


def get_optimized_classifications(farm_id=None, user_id=None, limit=None):
    """
    Exemple de fonction optimisée pour récupérer des classifications.
    
    Args:
        farm_id: ID de la ferme optionnel
        user_id: ID de l'utilisateur optionnel
        limit: Limite optionnelle du nombre de résultats
        
    Returns:
        QuerySet: QuerySet optimisé de PlumClassification
    """
    from plum_classifier.models import PlumClassification
    
    queryset = PlumClassification.objects.all()
    
    # Appliquer les filtres
    if farm_id:
        queryset = queryset.filter(farm_id=farm_id)
    if user_id:
        queryset = queryset.filter(uploaded_by_id=user_id)
    
    # Optimiser le queryset
    queryset = optimize_queryset(
        queryset,
        select_related=['uploaded_by', 'farm', 'batch'],
        prefetch_related=[]
    )
    
    # Appliquer la limite si spécifiée
    if limit:
        queryset = queryset[:limit]
        
    return queryset
