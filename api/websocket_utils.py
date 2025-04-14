"""
Utilitaires pour envoyer des messages via WebSockets.
"""

import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

channel_layer = get_channel_layer()

def send_notification(user_id, notification_type, title, message, data=None):
    """
    Envoie une notification en temps réel à un utilisateur spécifique.
    
    Args:
        user_id: ID de l'utilisateur destinataire
        notification_type: Type de notification (classification, batch_complete, account, system)
        title: Titre de la notification
        message: Contenu de la notification
        data: Données supplémentaires (optionnel)
    """
    group_name = f"notifications_{user_id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': timezone.now().isoformat()
        }
    )

def send_classification_result(user_id, image_id, predicted_class, confidence, probabilities=None, processing_time=None):
    """
    Envoie un résultat de classification en temps réel à un utilisateur spécifique.
    
    Args:
        user_id: ID de l'utilisateur destinataire
        image_id: ID de l'image classifiée
        predicted_class: Classe prédite
        confidence: Score de confiance
        probabilities: Probabilités pour chaque classe (optionnel)
        processing_time: Temps de traitement en ms (optionnel)
    """
    group_name = f"classifications_{user_id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'classification_result',
            'image_id': str(image_id),
            'predicted_class': predicted_class,
            'confidence': confidence,
            'probabilities': probabilities or {},
            'processing_time': processing_time,
            'timestamp': timezone.now().isoformat()
        }
    )

def send_batch_progress(user_id, batch_id, total_images, processed_images, status):
    """
    Envoie une mise à jour de progression de traitement par lot en temps réel.
    
    Args:
        user_id: ID de l'utilisateur destinataire
        batch_id: ID du lot
        total_images: Nombre total d'images dans le lot
        processed_images: Nombre d'images traitées
        status: Statut du traitement (pending, processing, completed, failed)
    """
    group_name = f"classifications_{user_id}"
    batch_group = f"batch_{batch_id}"
    
    # Calculer le pourcentage de progression
    progress_percentage = int((processed_images / total_images) * 100) if total_images > 0 else 0
    
    message = {
        'type': 'batch_progress',
        'batch_id': str(batch_id),
        'total_images': total_images,
        'processed_images': processed_images,
        'progress_percentage': progress_percentage,
        'status': status,
        'timestamp': timezone.now().isoformat()
    }
    
    # Envoyer au groupe de l'utilisateur
    async_to_sync(channel_layer.group_send)(group_name, message)
    
    # Envoyer au groupe spécifique du lot
    async_to_sync(channel_layer.group_send)(batch_group, message)

def send_stats_update(user_id, stats_type, data):
    """
    Envoie une mise à jour des statistiques du tableau de bord en temps réel.
    
    Args:
        user_id: ID de l'utilisateur destinataire
        stats_type: Type de statistiques (daily, weekly, monthly, etc.)
        data: Données des statistiques
    """
    group_name = f"dashboard_{user_id}"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'stats_update',
            'stats_type': stats_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
    )

def send_global_stats_update(stats_type, data):
    """
    Envoie une mise à jour des statistiques globales aux administrateurs.
    
    Args:
        stats_type: Type de statistiques (system, users, classifications, etc.)
        data: Données des statistiques
    """
    group_name = "global_stats"
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'global_stats_update',
            'stats_type': stats_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }
    )
