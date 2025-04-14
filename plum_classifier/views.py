"""
Vues pour l'application plum_classifier.
"""

from rest_framework import viewsets, status, permissions
from api.permissions import IsAdmin, IsAgriculteur, IsTechnicien, IsConsultant, IsOwnerOrAdmin, IsVerifiedUser, RoleBasedPermission
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import PlumImage, ClassificationResult, BatchClassificationJob, ModelMetrics
from .serializers import (
    PlumImageSerializer, ClassificationResultSerializer, BatchClassificationJobSerializer,
    ModelMetricsSerializer, ClassifyImageSerializer, BatchClassifySerializer
)
from .services.image_service import ImageService
from .services.model_service import ModelService
from api.websocket_utils import send_notification


class PlumImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les images de prunes.
    """
    serializer_class = PlumImageSerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien'],
        read_roles=['consultant']
    )]
    
    def get_queryset(self):
        """
        Retourne les images de l'utilisateur actuel ou toutes les images pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return PlumImage.objects.all().order_by('-uploaded_at')
        return PlumImage.objects.filter(user=user).order_by('-uploaded_at')
    
    @action(detail=True, methods=['post'])
    def classify(self, request, pk=None):
        """
        Classifie une image existante.
        """
        plum_image = self.get_object()
        
        try:
            # Vérifier si l'image a déjà été classifiée
            existing_classification = ClassificationResult.objects.filter(plum_image=plum_image).first()
            if existing_classification:
                serializer = ClassificationResultSerializer(
                    existing_classification, 
                    context={'request': request}
                )
                return Response(serializer.data)
            
            # Classifier l'image
            result = ImageService.classify_image(plum_image)
            
            # Récupérer le résultat de classification
            classification = ClassificationResult.objects.get(plum_image=plum_image)
            serializer = ClassificationResultSerializer(
                classification, 
                context={'request': request}
            )
            
            # Envoyer une notification
            send_notification(
                user_id=str(request.user.id),
                notification_type='classification',
                title='Classification terminée',
                message=f'Votre image a été classifiée comme {result["class_name"]} avec une confiance de {result["confidence"]:.2f}',
                data={'classification_id': str(classification.id), 'image_id': str(plum_image.id)}
            )
            
            return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def classify_new(self, request):
        """
        Upload et classifie une nouvelle image.
        """
        serializer = ClassifyImageSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Sauvegarder l'image
                plum_image = ImageService.save_image(
                    image_data=serializer.validated_data['image'],
                    user=request.user,
                    location=serializer.validated_data.get('location'),
                    notes=serializer.validated_data.get('notes'),
                    ground_truth=serializer.validated_data.get('ground_truth')
                )
                
                # Classifier l'image
                result = ImageService.classify_image(
                    plum_image=plum_image,
                    save_result=serializer.validated_data.get('save_result', True),
                    send_realtime=serializer.validated_data.get('send_realtime', True)
                )
                
                # Récupérer le résultat de classification
                classification = ClassificationResult.objects.get(plum_image=plum_image)
                result_serializer = ClassificationResultSerializer(
                    classification, 
                    context={'request': request}
                )
                
                # Envoyer une notification
                send_notification(
                    user_id=str(request.user.id),
                    notification_type='classification',
                    title='Classification terminée',
                    message=f'Votre image a été classifiée comme {result["class_name"]} avec une confiance de {result["confidence"]:.2f}',
                    data={'classification_id': str(classification.id), 'image_id': str(plum_image.id)}
                )
                
                return Response(result_serializer.data)
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClassificationResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les résultats de classification.
    """
    serializer_class = ClassificationResultSerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien'],
        read_roles=['consultant']
    )]
    
    def get_queryset(self):
        """
        Retourne les résultats de classification de l'utilisateur actuel ou tous les résultats pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return ClassificationResult.objects.all().order_by('-classified_at')
        return ClassificationResult.objects.filter(plum_image__user=user).order_by('-classified_at')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Retourne des statistiques sur les classifications de l'utilisateur.
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Statistiques globales
        total_count = queryset.count()
        class_counts = {}
        for choice in PlumImage.CATEGORY_CHOICES:
            class_counts[choice[0]] = queryset.filter(predicted_class=choice[0]).count()
        
        # Statistiques par période
        now = timezone.now()
        last_week = now - timezone.timedelta(days=7)
        last_month = now - timezone.timedelta(days=30)
        
        weekly_count = queryset.filter(classified_at__gte=last_week).count()
        monthly_count = queryset.filter(classified_at__gte=last_month).count()
        
        # Confiance moyenne
        avg_confidence = queryset.values_list('confidence', flat=True).aggregate(avg=models.Avg('confidence'))
        
        return Response({
            'total_count': total_count,
            'class_distribution': class_counts,
            'weekly_count': weekly_count,
            'monthly_count': monthly_count,
            'avg_confidence': avg_confidence['avg'] if avg_confidence['avg'] else 0
        })


class BatchClassificationJobViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les tâches de classification par lot.
    """
    serializer_class = BatchClassificationJobSerializer
    permission_classes = [IsVerifiedUser, RoleBasedPermission(
        allowed_roles=['admin', 'agriculteur', 'technicien'],
        read_roles=['consultant']
    )]
    
    def get_queryset(self):
        """
        Retourne les tâches de l'utilisateur actuel ou toutes les tâches pour les administrateurs.
        """
        user = self.request.user
        if user.is_admin:
            return BatchClassificationJob.objects.all().order_by('-created_at')
        return BatchClassificationJob.objects.filter(user=user).order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def start_batch(self, request):
        """
        Démarre une nouvelle tâche de classification par lot.
        """
        serializer = BatchClassifySerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Créer la tâche de classification par lot
                batch_job = BatchClassificationJob.objects.create(
                    user=request.user,
                    status=BatchClassificationJob.PENDING
                )
                
                # Déterminer les images à traiter
                if serializer.validated_data.get('all_unclassified', False):
                    # Toutes les images non classifiées
                    image_ids = PlumImage.objects.filter(
                        user=request.user
                    ).exclude(
                        id__in=ClassificationResult.objects.values_list('plum_image_id', flat=True)
                    ).values_list('id', flat=True)
                else:
                    # Images spécifiées
                    image_ids = serializer.validated_data.get('image_ids', [])
                
                # Mettre à jour le nombre total d'images
                batch_job.total_images = len(image_ids)
                batch_job.save(update_fields=['total_images'])
                
                # Démarrer le traitement (dans un thread séparé ou une tâche asynchrone)
                # Note: Dans une implémentation réelle, cela serait fait avec Celery ou un autre système de tâches
                # Pour cet exemple, nous allons simplement appeler la méthode directement
                ImageService.process_batch(batch_job)
                
                # Retourner la tâche créée
                serializer = BatchClassificationJobSerializer(
                    batch_job, 
                    context={'request': request}
                )
                return Response(serializer.data)
            
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModelMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les métriques du modèle.
    """
    serializer_class = ModelMetricsSerializer
    queryset = ModelMetrics.objects.all().order_by('-deployed_at')
    permission_classes = [IsAdmin]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Retourne les métriques du modèle actuel.
        """
        model_service = ModelService()
        model_info = model_service.get_model_info()
        
        # Récupérer les métriques du modèle en base de données
        latest_metrics = ModelMetrics.objects.order_by('-deployed_at').first()
        
        if latest_metrics:
            serializer = ModelMetricsSerializer(latest_metrics)
            metrics_data = serializer.data
        else:
            metrics_data = {}
        
        # Combiner avec les informations du modèle chargé
        response_data = {
            **model_info,
            **metrics_data
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def reload_model(self, request):
        """
        Recharge le modèle à partir du fichier .pt.
        """
        if not request.user.is_admin:
            return Response(
                {'error': 'Seuls les administrateurs peuvent recharger le modèle'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            model_service = ModelService()
            success = model_service.reload_model()
            
            if success:
                return Response({'status': 'Modèle rechargé avec succès'})
            else:
                return Response(
                    {'error': 'Échec du rechargement du modèle'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
