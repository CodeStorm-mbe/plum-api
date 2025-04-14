"""
Consommateurs WebSocket pour les mises à jour en temps réel.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consommateur WebSocket pour les notifications en temps réel.
    """
    
    async def connect(self):
        """
        Appelé lorsqu'un client WebSocket se connecte.
        """
        self.user = self.scope["user"]
        
        # Vérifier si l'utilisateur est authentifié
        if self.user.is_anonymous:
            # Rejeter la connexion
            await self.close()
            return
        
        # Créer un groupe spécifique à l'utilisateur pour les notifications
        self.notification_group_name = f"notifications_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.notification_group_name,
            self.channel_name
        )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté au service de notifications en temps réel'
        }))
    
    async def disconnect(self, close_code):
        """
        Appelé lorsqu'un client WebSocket se déconnecte.
        """
        # Quitter le groupe
        if hasattr(self, 'notification_group_name'):
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Appelé lorsqu'un message est reçu du client WebSocket.
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # Traiter différents types de messages
            if message_type == 'read_notification':
                notification_id = text_data_json.get('notification_id')
                if notification_id:
                    # Marquer la notification comme lue
                    success = await self.mark_notification_as_read(notification_id)
                    await self.send(text_data=json.dumps({
                        'type': 'notification_read_status',
                        'notification_id': notification_id,
                        'success': success
                    }))
            
            elif message_type == 'subscribe_to_classification':
                # Ajouter l'utilisateur au groupe de classification
                classification_group = "classification_updates"
                await self.channel_layer.group_add(
                    classification_group,
                    self.channel_name
                )
                await self.send(text_data=json.dumps({
                    'type': 'subscription_status',
                    'group': 'classification_updates',
                    'status': 'subscribed'
                }))
            
            elif message_type == 'ping':
                # Simple ping-pong pour vérifier la connexion
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
        
        except json.JSONDecodeError:
            # Ignorer les messages non-JSON
            pass
    
    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """
        Marque une notification comme lue dans la base de données.
        """
        from api.models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    async def notification_message(self, event):
        """
        Gestionnaire pour les messages de notification.
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
            'data': event.get('data', {}),
            'timestamp': event['timestamp']
        }))


class ClassificationConsumer(AsyncWebsocketConsumer):
    """
    Consommateur WebSocket pour les mises à jour de classification en temps réel.
    """
    
    async def connect(self):
        """
        Appelé lorsqu'un client WebSocket se connecte.
        """
        self.user = self.scope["user"]
        
        # Vérifier si l'utilisateur est authentifié
        if self.user.is_anonymous:
            # Rejeter la connexion
            await self.close()
            return
        
        # Créer un groupe spécifique à l'utilisateur pour les classifications
        self.classification_group_name = f"classifications_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.classification_group_name,
            self.channel_name
        )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté au service de classification en temps réel'
        }))
    
    async def disconnect(self, close_code):
        """
        Appelé lorsqu'un client WebSocket se déconnecte.
        """
        # Quitter le groupe
        if hasattr(self, 'classification_group_name'):
            await self.channel_layer.group_discard(
                self.classification_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Appelé lorsqu'un message est reçu du client WebSocket.
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # Traiter différents types de messages
            if message_type == 'subscribe_to_batch':
                batch_id = text_data_json.get('batch_id')
                if batch_id:
                    # Vérifier que l'utilisateur a accès à ce lot
                    has_access = await self.check_batch_access(batch_id)
                    if has_access:
                        # Ajouter l'utilisateur au groupe de ce lot
                        batch_group = f"batch_{batch_id}"
                        await self.channel_layer.group_add(
                            batch_group,
                            self.channel_name
                        )
                        await self.send(text_data=json.dumps({
                            'type': 'subscription_status',
                            'group': f'batch_{batch_id}',
                            'status': 'subscribed'
                        }))
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'error',
                            'message': 'Accès refusé à ce lot'
                        }))
            
            elif message_type == 'ping':
                # Simple ping-pong pour vérifier la connexion
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
        
        except json.JSONDecodeError:
            # Ignorer les messages non-JSON
            pass
    
    @database_sync_to_async
    def check_batch_access(self, batch_id):
        """
        Vérifie si l'utilisateur a accès à un lot spécifique.
        """
        from plum_classifier.models import BatchClassificationJob
        try:
            batch = BatchClassificationJob.objects.get(id=batch_id)
            return batch.user == self.user or self.user.is_admin
        except BatchClassificationJob.DoesNotExist:
            return False
    
    async def classification_result(self, event):
        """
        Gestionnaire pour les messages de résultat de classification.
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'classification_result',
            'image_id': event['image_id'],
            'predicted_class': event['predicted_class'],
            'confidence': event['confidence'],
            'probabilities': event.get('probabilities', {}),
            'processing_time': event.get('processing_time'),
            'timestamp': event['timestamp']
        }))
    
    async def batch_progress(self, event):
        """
        Gestionnaire pour les messages de progression de lot.
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'batch_progress',
            'batch_id': event['batch_id'],
            'total_images': event['total_images'],
            'processed_images': event['processed_images'],
            'progress_percentage': event['progress_percentage'],
            'status': event['status'],
            'timestamp': event['timestamp']
        }))


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    Consommateur WebSocket pour les mises à jour du tableau de bord en temps réel.
    """
    
    async def connect(self):
        """
        Appelé lorsqu'un client WebSocket se connecte.
        """
        self.user = self.scope["user"]
        
        # Vérifier si l'utilisateur est authentifié
        if self.user.is_anonymous:
            # Rejeter la connexion
            await self.close()
            return
        
        # Vérifier si l'utilisateur est administrateur pour certains groupes
        is_admin = await self.is_admin_user()
        
        # Créer un groupe pour les mises à jour du tableau de bord
        self.dashboard_group_name = f"dashboard_{self.user.id}"
        
        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        # Si l'utilisateur est administrateur, rejoindre le groupe des statistiques globales
        if is_admin:
            await self.channel_layer.group_add(
                "global_stats",
                self.channel_name
            )
        
        # Accepter la connexion
        await self.accept()
        
        # Envoyer un message de bienvenue
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connecté au service de tableau de bord en temps réel',
            'is_admin': is_admin
        }))
    
    async def disconnect(self, close_code):
        """
        Appelé lorsqu'un client WebSocket se déconnecte.
        """
        # Quitter les groupes
        if hasattr(self, 'dashboard_group_name'):
            await self.channel_layer.group_discard(
                self.dashboard_group_name,
                self.channel_name
            )
        
        is_admin = await self.is_admin_user()
        if is_admin:
            await self.channel_layer.group_discard(
                "global_stats",
                self.channel_name
            )
    
    @database_sync_to_async
    def is_admin_user(self):
        """
        Vérifie si l'utilisateur est un administrateur.
        """
        return self.user.is_admin
    
    async def receive(self, text_data):
        """
        Appelé lorsqu'un message est reçu du client WebSocket.
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # Traiter différents types de messages
            if message_type == 'subscribe_to_stats':
                # Déjà abonné aux statistiques appropriées lors de la connexion
                await self.send(text_data=json.dumps({
                    'type': 'subscription_status',
                    'group': 'dashboard_stats',
                    'status': 'subscribed'
                }))
            
            elif message_type == 'ping':
                # Simple ping-pong pour vérifier la connexion
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
        
        except json.JSONDecodeError:
            # Ignorer les messages non-JSON
            pass
    
    async def stats_update(self, event):
        """
        Gestionnaire pour les mises à jour de statistiques.
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats_type': event['stats_type'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
    
    async def global_stats_update(self, event):
        """
        Gestionnaire pour les mises à jour de statistiques globales (admin uniquement).
        """
        # Envoyer le message au client WebSocket
        await self.send(text_data=json.dumps({
            'type': 'global_stats_update',
            'stats_type': event['stats_type'],
            'data': event['data'],
            'timestamp': event['timestamp']
        }))
