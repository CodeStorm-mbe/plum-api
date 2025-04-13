from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .models import Farm, UserSettings
from .serializers import (
    UserSerializer, 
    FarmSerializer, 
    UserSettingsSerializer, 
    UserProfileSerializer
)
from .permissions import (
    IsOwnerOrAdmin, 
    IsAdminUser, 
    IsAuthenticatedAndVerified
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs avec documentation améliorée et contrôles d'accès.
    
    Permet de créer, lire, mettre à jour et supprimer des utilisateurs, avec des
    endpoints supplémentaires pour les profils et les paramètres.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'role']
    ordering_fields = ['username', 'email', 'created_at', 'role']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Retourne la classe de sérialiseur appropriée en fonction de l'action.
        """
        if self.action == 'me':
            return UserProfileSerializer
        return super().get_serializer_class()
    
    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action.
        - Les administrateurs peuvent tout faire
        - Les utilisateurs peuvent voir et modifier leur propre profil
        - Seuls les administrateurs peuvent créer ou supprimer des utilisateurs
        """
        if self.action in ['create', 'destroy', 'list']:
            permission_classes = [IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            permission_classes = [IsOwnerOrAdmin]
        elif self.action in ['me', 'settings']:
            permission_classes = [IsAuthenticatedAndVerified]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtre les utilisateurs en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir tous les utilisateurs.
        """
        user = self.request.user
        queryset = User.objects.all()
        
        # Filtrage par rôle si spécifié dans les paramètres de requête
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filtrage par vérification d'email si spécifié
        verified = self.request.query_params.get('verified', None)
        if verified is not None:
            is_verified = verified.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(email_verified=is_verified)
        
        # Les utilisateurs normaux ne peuvent voir que leur propre profil
        if not (user.is_staff or user.is_admin_user):
            queryset = queryset.filter(id=user.id)
        
        return queryset
    
    @extend_schema(
        summary="Obtenir le profil de l'utilisateur connecté",
        description="Retourne les informations détaillées du profil de l'utilisateur actuellement connecté.",
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Retourne le profil de l'utilisateur connecté.
        """
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Gérer les paramètres de l'utilisateur",
        description="Permet de consulter et modifier les paramètres de l'utilisateur connecté.",
        responses={
            200: UserSettingsSerializer,
            400: {"description": "Données invalides"}
        }
    )
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
        serializer = UserSettingsSerializer(
            user_settings, 
            data=request.data, 
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Statistiques des utilisateurs",
        description="Retourne des statistiques sur les utilisateurs (admin seulement).",
        responses={
            200: {"description": "Statistiques des utilisateurs"},
            403: {"description": "Permission refusée"}
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """
        Retourne des statistiques sur les utilisateurs (admin seulement).
        """
        total_users = User.objects.count()
        role_counts = User.objects.values('role').annotate(count=Count('id'))
        verified_count = User.objects.filter(email_verified=True).count()
        
        # Statistiques supplémentaires
        active_users = User.objects.filter(is_active=True).count()
        recent_users = User.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'recent_users': recent_users,
            'role_distribution': {item['role']: item['count'] for item in role_counts},
            'verified_users': verified_count,
            'verification_rate': (verified_count / total_users) * 100 if total_users > 0 else 0
        })
    
    def perform_create(self, serializer):
        """
        Enregistre l'adresse IP lors de la création d'un utilisateur.
        """
        # Récupérer l'adresse IP du client
        ip = self.request.META.get('REMOTE_ADDR')
        serializer.save(last_login_ip=ip)
    
    def perform_update(self, serializer):
        """
        Vérifie les permissions avant de mettre à jour un utilisateur.
        """
        user = self.get_object()
        request_user = self.request.user
        
        # Vérifier si l'utilisateur essaie de changer son propre rôle
        if 'role' in serializer.validated_data and user.id == request_user.id:
            new_role = serializer.validated_data['role']
            if new_role != user.role and new_role == User.Roles.ADMIN:
                raise PermissionDenied(_("Vous ne pouvez pas vous promouvoir vous-même au rôle d'administrateur."))
        
        serializer.save()


class FarmViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des fermes avec documentation améliorée et contrôles d'accès.
    
    Permet de créer, lire, mettre à jour et supprimer des fermes, avec des
    endpoints supplémentaires pour les statistiques et les lots.
    """
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'description', 'owner__username']
    ordering_fields = ['name', 'created_at', 'size']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filtre les fermes en fonction de l'utilisateur connecté.
        Les administrateurs peuvent voir toutes les fermes.
        """
        user = self.request.user
        queryset = Farm.objects.all()
        
        # Filtrage par taille si spécifié
        min_size = self.request.query_params.get('min_size', None)
        max_size = self.request.query_params.get('max_size', None)
        
        if min_size:
            try:
                queryset = queryset.filter(size__gte=float(min_size))
            except ValueError:
                pass
        
        if max_size:
            try:
                queryset = queryset.filter(size__lte=float(max_size))
            except ValueError:
                pass
        
        # Filtrage par propriétaire si spécifié
        owner_id = self.request.query_params.get('owner', None)
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        
        # Les utilisateurs normaux ne voient que leurs propres fermes
        if not (user.is_staff or user.is_admin_user):
            queryset = queryset.filter(owner=user)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Définit l'utilisateur connecté comme propriétaire de la ferme.
        """
        serializer.save(owner=self.request.user)
    
    @extend_schema(
        summary="Statistiques de la ferme",
        description="Retourne des statistiques sur les classifications pour une ferme spécifique.",
        responses={200: {"description": "Statistiques de la ferme"}}
    )
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
                'farm_id': str(farm.id),
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
                    'batch_id': str(batch.id),
                    'batch_name': batch.name,
                    'total_classifications': batch_count,
                    'quality_distribution': batch.quality_distribution
                })
        
        return Response({
            'farm_id': str(farm.id),
            'farm_name': farm.name,
            'total_classifications': total_classifications,
            'class_counts': class_counts,
            'class_percentages': class_percentages,
            'average_confidence': avg_confidence,
            'batches': batch_stats
        })
    
    @extend_schema(
        summary="Lots de la ferme",
        description="Retourne tous les lots pour une ferme spécifique.",
        responses={200: {"description": "Liste des lots de la ferme"}}
    )
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
    
    @extend_schema(
        summary="Fermes à proximité",
        description="Retourne les fermes à proximité d'une position géographique donnée.",
        parameters=[
            OpenApiParameter(name='lat', description='Latitude', required=True, type=float),
            OpenApiParameter(name='lng', description='Longitude', required=True, type=float),
            OpenApiParameter(name='radius', description='Rayon en kilomètres', required=False, type=float, default=10.0),
        ],
        responses={200: {"description": "Liste des fermes à proximité"}}
    )
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Retourne les fermes à proximité d'une position géographique donnée.
        """
        try:
            lat = float(request.query_params.get('lat', 0))
            lng = float(request.query_params.get('lng', 0))
            radius = float(request.query_params.get('radius', 10.0))  # Rayon en km
        except (ValueError, TypeError):
            return Response(
                {"error": "Paramètres de position invalides. Veuillez fournir lat, lng et radius (optionnel) valides."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrer les fermes avec des coordonnées
        farms = Farm.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        # Calculer les fermes à proximité
        # Note: Cette méthode est approximative et fonctionne bien pour de petites distances
        # Pour une solution plus précise, utiliser PostGIS ou une bibliothèque géospatiale
        from math import cos, radians
        
        # Conversion du rayon en degrés (approximation)
        lat_radius = radius / 111.0  # 1 degré de latitude ≈ 111 km
        lng_radius = radius / (111.0 * cos(radians(lat)))  # Ajustement pour la longitude
        
        nearby_farms = farms.filter(
            latitude__gte=lat - lat_radius,
            latitude__lte=lat + lat_radius,
            longitude__gte=lng - lng_radius,
            longitude__lte=lng + lng_radius
        )
        
        serializer = self.get_serializer(nearby_farms, many=True)
        return Response(serializer.data)
