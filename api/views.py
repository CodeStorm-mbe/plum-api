"""
Vues pour l'application api.
"""

from rest_framework import viewsets, status, permissions
from api.permissions import IsAdmin, IsAgriculteur, IsTechnicien, IsConsultant, IsOwnerOrAdmin, IsVerifiedUser, RoleBasedPermission
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import ApiKey, ApiLog, Notification, Feedback
from .serializers import (
    ApiKeySerializer, ApiLogSerializer, NotificationSerializer,
    FeedbackSerializer, DashboardStatsSerializer
)
from plum_classifier.models import PlumImage, ClassificationResult, BatchClassificationJob
from api.websocket_utils import send_notification, send_stats_update

User = get_user_model()


class ApiKeyViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les clés API.
    """
    serializer_class = ApiKeySerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien'],
        read_roles=[]
    )]
    
    def get_queryset(self):
        """
        Retourne les clés API de l'utilisateur actuel ou toutes les clés pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return ApiKey.objects.all().order_by('-created_at')
        return ApiKey.objects.filter(user=user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """
        Régénère une clé API existante.
        """
        api_key = self.get_object()
        api_key.key = uuid.uuid4()
        api_key.save(update_fields=['key'])
        
        serializer = self.get_serializer(api_key)
        return Response(serializer.data)


class ApiLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les logs d'API.
    """
    serializer_class = ApiLogSerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin'],
        read_roles=['technicien']
    )]
    
    def get_queryset(self):
        """
        Retourne les logs d'API de l'utilisateur actuel ou tous les logs pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return ApiLog.objects.all().order_by('-timestamp')
        return ApiLog.objects.filter(user=user).order_by('-timestamp')


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsVerifiedUser]
    
    def get_queryset(self):
        """
        Retourne les notifications de l'utilisateur actuel.
        """
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marque une notification comme lue.
        """
        notification = self.get_object()
        notification.mark_as_read()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Marque toutes les notifications de l'utilisateur comme lues.
        """
        now = timezone.now()
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        
        notifications.update(is_read=True, read_at=now)
        
        return Response({'status': f'{count} notifications marquées comme lues'})


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les feedbacks sur les classifications.
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien', 'consultant'],
        read_roles=[]
    )]
    
    def get_queryset(self):
        """
        Retourne les feedbacks de l'utilisateur actuel ou tous les feedbacks pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return Feedback.objects.all().order_by('-created_at')
        return Feedback.objects.filter(user=user).order_by('-created_at')


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet pour le tableau de bord.
    """
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien'],
        read_roles=['consultant']
    )]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourne les statistiques pour le tableau de bord.
        """
        user = request.user
        
        # Filtrer les données selon le rôle de l'utilisateur
        if user.is_admin:
            images = PlumImage.objects.all()
            classifications = ClassificationResult.objects.all()
        else:
            images = PlumImage.objects.filter(user=user)
            classifications = ClassificationResult.objects.filter(plum_image__user=user)
        
        # Statistiques de base
        total_images = images.count()
        total_classifications = classifications.count()
        
        # Classifications récentes (7 derniers jours)
        last_week = timezone.now() - timezone.timedelta(days=7)
        recent_classifications = classifications.filter(classified_at__gte=last_week).count()
        
        # Distribution des classifications par classe
        class_distribution = {}
        for choice in PlumImage.CATEGORY_CHOICES:
            class_distribution[choice[0]] = classifications.filter(predicted_class=choice[0]).count()
        
        # Confiance moyenne
        avg_confidence = classifications.aggregate(avg=Avg('confidence'))['avg'] or 0
        
        # Statistiques utilisateur (admin uniquement)
        user_stats = {}
        if user.is_admin:
            user_stats['total_users'] = User.objects.count()
            user_stats['active_users'] = User.objects.filter(is_active=True).count()
            user_stats['admin_users'] = User.objects.filter(role=User.ADMIN).count()
            user_stats['agriculteur_users'] = User.objects.filter(role=User.AGRICULTEUR).count()
            user_stats['technicien_users'] = User.objects.filter(role=User.TECHNICIEN).count()
            user_stats['consultant_users'] = User.objects.filter(role=User.CONSULTANT).count()
        
        # Préparer les données de réponse
        data = {
            'total_images': total_images,
            'total_classifications': total_classifications,
            'recent_classifications': recent_classifications,
            'classification_distribution': class_distribution,
            'avg_confidence': avg_confidence
        }
        
        if user.is_admin:
            data['user_stats'] = user_stats
        
        # Sérialiser et retourner les données
        serializer = DashboardStatsSerializer(data)
        
        # Envoyer une mise à jour en temps réel (optionnel)
        send_stats_update(
            user_id=str(user.id),
            stats_type='dashboard',
            data=data
        )
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """
        Retourne l'activité récente pour le tableau de bord.
        """
        user = request.user
        
        # Filtrer les données selon le rôle de l'utilisateur
        if user.is_admin:
            recent_classifications = ClassificationResult.objects.all()
            recent_uploads = PlumImage.objects.all()
            recent_batches = BatchClassificationJob.objects.all()
        else:
            recent_classifications = ClassificationResult.objects.filter(plum_image__user=user)
            recent_uploads = PlumImage.objects.filter(user=user)
            recent_batches = BatchClassificationJob.objects.filter(user=user)
        
        # Limiter aux 10 éléments les plus récents
        recent_classifications = recent_classifications.order_by('-classified_at')[:10]
        recent_uploads = recent_uploads.order_by('-uploaded_at')[:10]
        recent_batches = recent_batches.order_by('-updated_at')[:10]
        
        # Préparer les données de réponse
        from plum_classifier.serializers import (
            ClassificationResultSerializer, PlumImageSerializer, BatchClassificationJobSerializer
        )
        
        data = {
            'recent_classifications': ClassificationResultSerializer(
                recent_classifications, many=True, context={'request': request}
            ).data,
            'recent_uploads': PlumImageSerializer(
                recent_uploads, many=True, context={'request': request}
            ).data,
            'recent_batches': BatchClassificationJobSerializer(
                recent_batches, many=True, context={'request': request}
            ).data
        }
        
        return Response(data)
