from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import DashboardMetric, DashboardPreference
from .serializers import (
    DashboardMetricSerializer, 
    DashboardPreferenceSerializer,
    AdminDashboardSerializer,
    TechnicianDashboardSerializer,
    FarmerDashboardSerializer
)
from users.models import User, Farm
from plum_classifier.models import PlumClassification, PlumBatch, ModelVersion
from plum_classifier.serializers import PlumClassificationSerializer

class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet pour les données du dashboard.
    """
    
    def get_permissions(self):
        """
        Définit les permissions en fonction de l'action.
        """
        if self.action in ['admin_dashboard']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def user_dashboard(self, request):
        """
        Retourne les données du dashboard adaptées au rôle de l'utilisateur.
        """
        user = request.user
        role = user.role
        
        if role == 'admin':
            return self.admin_dashboard(request)
        elif role == 'technician':
            return self.technician_dashboard(request)
        else:  # farmer ou autre
            return self.farmer_dashboard(request)
    
    @action(detail=False, methods=['get'])
    def admin_dashboard(self, request):
        """
        Retourne les données du dashboard pour les administrateurs.
        """
        # Récupérer les statistiques de classification
        classifications = PlumClassification.objects.all()
        total_classifications = classifications.count()
        
        # Calculer la confiance moyenne
        avg_confidence = 0
        if total_classifications > 0:
            avg_confidence = classifications.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
        
        # Calculer la distribution des classes
        class_counts = {}
        for classification in classifications:
            class_name = classification.get_class_name_display()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Calculer les pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total_classifications) * 100 if total_classifications > 0 else 0
            class_percentages[class_name] = round(percentage, 2)
        
        # Récupérer les classifications récentes
        recent_classifications = classifications.order_by('-created_at')[:10]
        recent_data = PlumClassificationSerializer(recent_classifications, many=True).data
        
        # Statistiques des utilisateurs
        users = User.objects.all()
        total_users = users.count()
        
        # Distribution par rôle
        users_by_role = {
            'admin': users.filter(role='admin').count(),
            'technician': users.filter(role='technician').count(),
            'farmer': users.filter(role='farmer').count(),
        }
        
        # Utilisateurs actifs (connectés dans les 30 derniers jours)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_users = users.filter(last_login__gte=thirty_days_ago).count()
        
        # Informations sur le modèle actif
        active_model = ModelVersion.objects.filter(is_active=True).first()
        model_info = {
            'version': active_model.version if active_model else 'Inconnue',
            'name': active_model.name if active_model else 'Inconnu',
            'accuracy': active_model.accuracy if active_model else 0,
        }
        
        # Performance du système
        system_performance = {
            'average_processing_time': classifications.aggregate(Avg('processing_time'))['processing_time__avg'] or 0,
            'api_response_time': 0.2,  # Valeur fictive, à remplacer par une mesure réelle
            'model_version': model_info['version'],
            'model_accuracy': model_info['accuracy'],
        }
        
        # Assembler les données
        dashboard_data = {
            'total_classifications': total_classifications,
            'average_confidence': avg_confidence,
            'class_distribution': class_counts,
            'class_percentages': class_percentages,
            'recent_classifications': recent_data,
            'total_users': total_users,
            'users_by_role': users_by_role,
            'active_users': active_users,
            'system_performance': system_performance,
        }
        
        serializer = AdminDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def technician_dashboard(self, request):
        """
        Retourne les données du dashboard pour les techniciens.
        """
        user = request.user
        
        # Récupérer les statistiques de classification
        # Pour un technicien, on pourrait filtrer selon les fermes qu'il gère
        # mais pour simplifier, on utilise toutes les classifications
        classifications = PlumClassification.objects.all()
        total_classifications = classifications.count()
        
        # Calculer la confiance moyenne
        avg_confidence = 0
        if total_classifications > 0:
            avg_confidence = classifications.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
        
        # Calculer la distribution des classes
        class_counts = {}
        for classification in classifications:
            class_name = classification.get_class_name_display()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Calculer les pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total_classifications) * 100 if total_classifications > 0 else 0
            class_percentages[class_name] = round(percentage, 2)
        
        # Récupérer les classifications récentes
        recent_classifications = classifications.order_by('-created_at')[:10]
        recent_data = PlumClassificationSerializer(recent_classifications, many=True).data
        
        # Fermes gérées (dans un cas réel, il faudrait une relation entre technicien et fermes)
        # Pour simplifier, on suppose que le technicien a accès à toutes les fermes
        farms = Farm.objects.all()
        managed_farms = farms.count()
        
        # Performance des fermes
        farm_performance = []
        for farm in farms:
            farm_classifications = classifications.filter(farm=farm)
            farm_total = farm_classifications.count()
            
            # Calculer les pourcentages par classe pour cette ferme
            farm_class_counts = {}
            for classification in farm_classifications:
                class_name = classification.get_class_name_display()
                farm_class_counts[class_name] = farm_class_counts.get(class_name, 0) + 1
            
            farm_class_percentages = {}
            for class_name, count in farm_class_counts.items():
                percentage = (count / farm_total) * 100 if farm_total > 0 else 0
                farm_class_percentages[class_name] = round(percentage, 2)
            
            farm_performance.append({
                'id': farm.id,
                'name': farm.name,
                'total_classifications': farm_total,
                'class_counts': farm_class_counts,
                'class_percentages': farm_class_percentages,
            })
        
        # Tendances de qualité (exemple simplifié)
        quality_trends = []
        categories = ['Bonne qualité', 'Non mûre', 'Tachetée', 'Fissurée', 'Meurtrie', 'Pourrie']
        
        for category in categories:
            trend = {
                'category': category,
                'data': []
            }
            
            for farm in farms:
                farm_classifications = classifications.filter(farm=farm)
                farm_total = farm_classifications.count()
                category_count = farm_classifications.filter(class_name__icontains=category.lower()).count()
                percentage = (category_count / farm_total) * 100 if farm_total > 0 else 0
                
                trend['data'].append({
                    'farm_id': farm.id,
                    'farm_name': farm.name,
                    'percentage': round(percentage, 2)
                })
            
            quality_trends.append(trend)
        
        # Assembler les données
        dashboard_data = {
            'total_classifications': total_classifications,
            'average_confidence': avg_confidence,
            'class_distribution': class_counts,
            'class_percentages': class_percentages,
            'recent_classifications': recent_data,
            'managed_farms': managed_farms,
            'farm_performance': farm_performance,
            'quality_trends': quality_trends,
        }
        
        serializer = TechnicianDashboardSerializer(dashboard_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def farmer_dashboard(self, request):
        """
        Retourne les données du dashboard pour les agriculteurs.
        """
        user = request.user
        
        # Récupérer les fermes de l'agriculteur
        farms = Farm.objects.filter(owner=user)
        
        # Récupérer les classifications pour les fermes de l'agriculteur
        classifications = PlumClassification.objects.filter(farm__in=farms)
        total_classifications = classifications.count()
        
        # Calculer la confiance moyenne
        avg_confidence = 0
        if total_classifications > 0:
            avg_confidence = classifications.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
        
        # Calculer la distribution des classes
        class_counts = {}
        for classification in classifications:
            class_name = classification.get_class_name_display()
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Calculer les pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total_classifications) * 100 if total_classifications > 0 else 0
            class_percentages[class_name] = round(percentage, 2)
        
        # Récupérer les classifications récentes
        recent_classifications = classifications.order_by('-created_at')[:10]
        recent_data = PlumClassificationSerializer(recent_classifications, many=True).data
        
        # Statistiques des fermes
        farm_stats = []
        total_batches = 0
        pending_batches = 0
        
        for farm in farms:
            farm_classifications = classifications.filter(farm=farm)
            farm_total = farm_classifications.count()
            
            # Calculer les pourcentages par classe pour cette ferme
            farm_class_counts = {}
            for classification in farm_classifications:
                class_name = classification.get_class_name_display()
                farm_class_counts[class_name] = farm_class_counts.get(class_name, 0) + 1
            
            farm_class_percentages = {}
            for class_name, count in farm_class_counts.items():
                percentage = (count / farm_total) * 100 if farm_total > 0 else 0
                farm_class_percentages[class_name] = round(percentage, 2)
            
            # Récupérer les lots de la ferme
            batches = PlumBatch.objects.filter(farm=farm)
            farm_batches = batches.count()
            farm_pending = batches.filter(status='pending').count()
            
            total_batches += farm_batches
            pending_batches += farm_pending
            
            farm_stats.append({
                'id': farm.id,
                'name': farm.name,
                'location': farm.location,
                'total_classifications': farm_total,
                'total_batches': farm_batches,
                'pending_batches': farm_pending,
                'class_counts': farm_class_counts,
                'class_percentages': farm_class_percentages,
            })
        
        # Assembler les données
        dashboard_data = {
            'total_classifications': total_classifications,
            'average_confidence': avg_confidence,
            'class_distribution': class_counts,
            'class_percentages': class_percentages,
            'recent_classifications': recent_data,
            'farms': farm_stats,
            'total_batches': total_batches,
            'pending_batches': pending_batches,
        }
        
        serializer = FarmerDashboardSerializer(dashboard_data)
        return Response(serializer.data)


class DashboardPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les préférences de dashboard des utilisateurs.
    """
    serializer_class = DashboardPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Retourne uniquement les préférences de l'utilisateur connecté.
        """
        return DashboardPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Associe l'utilisateur connecté aux préférences créées.
        """
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """
        Retourne les préférences de dashboard de l'utilisateur connecté.
        """
        preferences, created = DashboardPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preferences)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """
        Met à jour les préférences de dashboard de l'utilisateur connecté.
        """
        preferences, created = DashboardPreference.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
