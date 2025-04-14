from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os
import uuid
import logging
from django.utils import timezone

from .models import PlumClassification, PlumBatch, ModelVersion
from .serializers import PlumClassificationSerializer, PlumBatchSerializer, ModelVersionSerializer
from .services import PlumClassifierService

logger = logging.getLogger(__name__)

class PlumClassificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la classification des prunes.
    """
    queryset = PlumClassification.objects.all()
    serializer_class = PlumClassificationSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        """
        Filtre les classifications en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir toutes les classifications.
        """
        user = self.request.user
        if user.is_staff or user.is_admin_user:
            return PlumClassification.objects.all()
        
        # Les agriculteurs ne voient que leurs propres classifications
        if user.is_farmer:
            return PlumClassification.objects.filter(uploaded_by=user)
        
        # Les techniciens peuvent voir les classifications des fermes qu'ils gèrent
        # (cette logique serait à implémenter selon les besoins spécifiques)
        return PlumClassification.objects.filter(uploaded_by=user)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def classify(self, request):
        """
        Endpoint pour classifier une image de prune.
        """
        if 'image' not in request.FILES:
            return Response(
                {'error': 'Aucune image fournie'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        farm_id = request.data.get('farm_id')
        batch_id = request.data.get('batch_id')
        use_tta = request.data.get('use_tta', 'false').lower() == 'true'
        
        # Sauvegarder l'image
        filename = f"{uuid.uuid4()}.jpg"
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'plum_images')
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, filename)
        
        with open(image_path, 'wb+') as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)
        
        # Classifier l'image
        classifier = PlumClassifierService.get_instance()
        results = classifier.classify_image(image_path, tta=use_tta)
        
        if 'error' in results:
            return Response(
                {'error': results['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Enregistrer les résultats
        classification = PlumClassification(
            image_path=image_path,
            original_filename=image_file.name,
            uploaded_by=request.user,
            farm_id=farm_id,
            batch_id=batch_id,
            classification_result=results,
            class_name=results['class_name'],
            confidence_score=results['confidence'],
            is_plum=results['est_prune'],
            processing_time=results['processing_time'],
            device_info=request.META.get('HTTP_USER_AGENT', ''),
            geo_location=request.data.get('geo_location')
        )
        classification.save()
        
        # Retourner les résultats
        serializer = PlumClassificationSerializer(classification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourne des statistiques sur les classifications.
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Filtrer par période si spécifié
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Calculer les statistiques
        total_count = queryset.count()
        class_counts = {}
        
        for classification in queryset:
            class_name = classification.get_class_name_display()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Calculer les pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            class_percentages[class_name] = round(percentage, 2)
        
        # Calculer la confiance moyenne
        avg_confidence = 0
        if total_count > 0:
            avg_confidence = queryset.aggregate(models.Avg('confidence_score'))['confidence_score__avg']
        
        return Response({
            'total_classifications': total_count,
            'class_counts': class_counts,
            'class_percentages': class_percentages,
            'average_confidence': avg_confidence,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        })


class PlumBatchViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les lots de prunes.
    """
    queryset = PlumBatch.objects.all()
    serializer_class = PlumBatchSerializer
    
    def get_queryset(self):
        """
        Filtre les lots en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir tous les lots.
        """
        user = self.request.user
        if user.is_staff or user.is_admin_user:
            return PlumBatch.objects.all()
        
        # Les agriculteurs ne voient que leurs propres lots
        if user.is_farmer:
            return PlumBatch.objects.filter(farm__owner=user)
        
        # Les techniciens peuvent voir les lots des fermes qu'ils gèrent
        # (cette logique serait à implémenter selon les besoins spécifiques)
        return PlumBatch.objects.filter(created_by=user)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def classify_batch(self, request, pk=None):
        """
        Endpoint pour classifier un lot d'images de prunes.
        """
        batch = self.get_object()
        
        if 'images' not in request.FILES:
            return Response(
                {'error': 'Aucune image fournie'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        images = request.FILES.getlist('images')
        use_tta = request.data.get('use_tta', 'false').lower() == 'true'
        
        # Créer le répertoire pour les images
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'plum_images', f'batch_{batch.id}')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Classifier chaque image
        classifier = PlumClassifierService.get_instance()
        classifications = []
        
        for image_file in images:
            # Sauvegarder l'image
            filename = f"{uuid.uuid4()}.jpg"
            image_path = os.path.join(upload_dir, filename)
            
            with open(image_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)
            
            # Classifier l'image
            results = classifier.classify_image(image_path, tta=use_tta)
            
            if 'error' not in results:
                # Enregistrer les résultats
                classification = PlumClassification(
                    image_path=image_path,
                    original_filename=image_file.name,
                    uploaded_by=request.user,
                    farm=batch.farm,
                    batch=batch,
                    classification_result=results,
                    class_name=results['class_name'],
                    confidence_score=results['confidence'],
                    is_plum=results['est_prune'],
                    processing_time=results['processing_time'],
                    device_info=request.META.get('HTTP_USER_AGENT', ''),
                    geo_location=request.data.get('geo_location')
                )
                classification.save()
                classifications.append(classification)
        
        # Mettre à jour le résumé du lot
        batch.update_classification_summary()
        
        # Retourner les résultats
        return Response({
            'batch_id': batch.id,
            'total_processed': len(classifications),
            'total_images': len(images),
            'status': batch.status,
            'summary': batch.classification_summary
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def classifications(self, request, pk=None):
        """
        Retourne toutes les classifications d'un lot.
        """
        batch = self.get_object()
        classifications = batch.classifications.all()
        serializer = PlumClassificationSerializer(classifications, many=True)
        return Response(serializer.data)


class ModelVersionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les versions du modèle.
    """
    queryset = ModelVersion.objects.all()
    serializer_class = ModelVersionSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Active une version spécifique du modèle.
        """
        model_version = self.get_object()
        
        # Vérifier que le fichier existe
        if not os.path.exists(model_version.file_path):
            return Response(
                {'error': f"Le fichier de modèle n'existe pas: {model_version.file_path}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Désactiver tous les modèles
        ModelVersion.objects.all().update(is_active=False)
        
        # Activer le modèle sélectionné
        model_version.is_active = True
        model_version.save()
        
        # Recharger le modèle dans le service
        classifier = PlumClassifierService.get_instance()
        success = classifier.switch_model(model_version.id)
        
        if not success:
            return Response(
                {'error': "Impossible de charger le modèle"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': f"Modèle {model_version.name} v{model_version.version} activé avec succès",
            'model_info': classifier.get_model_info()
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Retourne la version active du modèle.
        """
        active_model = ModelVersion.objects.filter(is_active=True).first()
        
        if not active_model:
            return Response(
                {'message': "Aucun modèle actif"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(active_model)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def reload(self, request):
        """
        Force le rechargement du modèle actif.
        """
        classifier = PlumClassifierService.get_instance()
        success = classifier.reload_model()
        
        if not success:
            return Response(
                {'error': "Impossible de recharger le modèle"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': "Modèle rechargé avec succès",
            'model_info': classifier.get_model_info()
        })
    
    @action(detail=False, methods=['get'])
    def info(self, request):
        """
        Retourne des informations sur le modèle chargé.
        """
        classifier = PlumClassifierService.get_instance()
        model_info = classifier.get_model_info()
        
        return Response(model_info)
