from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg

from .models import Farm, UserSettings
from .serializers import UserSerializer, FarmSerializer, UserSettingsSerializer, UserProfileSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action.
        - Les administrateurs peuvent tout faire
        - Les utilisateurs peuvent voir et modifier leur propre profil
        - Seuls les administrateurs peuvent créer ou supprimer des utilisateurs
        """
        if self.action in ['create', 'destroy', 'list']:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update', 'me', 'settings']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtre les utilisateurs en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir tous les utilisateurs.
        """
        user = self.request.user
        if user.is_staff or user.is_admin_user:
            return User.objects.all()
        
        # Les utilisateurs normaux ne peuvent voir que leur propre profil
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Retourne le profil de l'utilisateur connecté.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def settings(self, request):
        """
        Récupère ou met à jour les paramètres de l'utilisateur connecté.
        """
        user_settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = UserSettingsSerializer(user_settings)
            return Response(serializer.data)
        
        # PUT ou PATCH
        serializer = UserSettingsSerializer(user_settings, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourne des statistiques sur les utilisateurs (admin seulement).
        """
        if not request.user.is_staff and not request.user.is_admin_user:
            return Response({"error": "Permission refusée"}, status=status.HTTP_403_FORBIDDEN)
        
        total_users = User.objects.count()
        role_counts = User.objects.values('role').annotate(count=Count('id'))
        verified_count = User.objects.filter(email_verified=True).count()
        
        return Response({
            'total_users': total_users,
            'role_distribution': {item['role']: item['count'] for item in role_counts},
            'verified_users': verified_count,
            'verification_rate': (verified_count / total_users) * 100 if total_users > 0 else 0
        })


class FarmViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des fermes.
    """
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    
    def get_queryset(self):
        """
        Filtre les fermes en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir toutes les fermes.
        """
        user = self.request.user
        if user.is_staff or user.is_admin_user:
            return Farm.objects.all()
        
        # Les agriculteurs ne voient que leurs propres fermes
        if user.is_farmer:
            return Farm.objects.filter(owner=user)
        
        # Les techniciens peuvent voir les fermes qu'ils gèrent
        # (cette logique serait à implémenter selon les besoins spécifiques)
        return Farm.objects.filter(owner=user)
    
    def perform_create(self, serializer):
        """
        Définit l'utilisateur connecté comme propriétaire de la ferme.
        """
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Retourne des statistiques sur les classifications pour une ferme spécifique.
        """
        farm = self.get_object()
        
        # Obtenir toutes les classifications pour cette ferme
        classifications = farm.classifications.all()
        
        # Statistiques de base
        total_classifications = classifications.count()
        
        if total_classifications == 0:
            return Response({
                'farm_id': farm.id,
                'farm_name': farm.name,
                'total_classifications': 0,
                'message': 'Aucune classification disponible pour cette ferme'
            })
        
        # Distribution des classes
        class_counts = {}
        for classification in classifications:
            class_name = classification.get_class_name_display()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total_classifications) * 100
            class_percentages[class_name] = round(percentage, 2)
        
        # Confiance moyenne
        avg_confidence = classifications.aggregate(Avg('confidence_score'))['confidence_score__avg']
        
        # Statistiques par lot
        batches = farm.batches.all()
        batch_stats = []
        
        for batch in batches:
            batch_classifications = batch.classifications.all()
            batch_count = batch_classifications.count()
            
            if batch_count > 0:
                batch_stats.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'total_classifications': batch_count,
                    'quality_distribution': batch.quality_distribution
                })
        
        return Response({
            'farm_id': farm.id,
            'farm_name': farm.name,
            'total_classifications': total_classifications,
            'class_counts': class_counts,
            'class_percentages': class_percentages,
            'average_confidence': avg_confidence,
            'batches': batch_stats
        })
    
    @action(detail=True, methods=['get'])
    def batches(self, request, pk=None):
        """
        Retourne tous les lots pour une ferme spécifique.
        """
        farm = self.get_object()
        batches = farm.batches.all()
        
        from plum_classifier.serializers import PlumBatchSerializer
        serializer = PlumBatchSerializer(batches, many=True)
        
        return Response(serializer.data)
