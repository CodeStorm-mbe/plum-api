"""
Module pour les fonctions d'analyse avancées du dashboard.
Fournit des outils pour générer des statistiques, des prédictions et des visualisations.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Q, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

from plum_classifier.models import PlumClassification, PlumBatch, ModelVersion
from users.models import Farm, User


class DashboardAnalytics:
    """
    Classe pour générer des analyses avancées pour le dashboard.
    """
    
    @staticmethod
    def get_time_series_data(queryset, date_field='created_at', period='day', value_field=None, 
                            group_by=None, start_date=None, end_date=None):
        """
        Génère des données de séries temporelles à partir d'un queryset.
        
        Args:
            queryset: Le queryset Django à analyser
            date_field: Le champ de date à utiliser pour la série temporelle
            period: La période d'agrégation ('day', 'week', 'month')
            value_field: Le champ à agréger (si None, compte les occurrences)
            group_by: Champ optionnel pour grouper les données
            start_date: Date de début optionnelle
            end_date: Date de fin optionnelle
            
        Returns:
            dict: Données de séries temporelles formatées
        """
        # Filtrer par date si spécifié
        if start_date:
            queryset = queryset.filter(**{f"{date_field}__gte": start_date})
        if end_date:
            queryset = queryset.filter(**{f"{date_field}__lte": end_date})
            
        # Déterminer la fonction de troncature selon la période
        if period == 'day':
            trunc_func = TruncDay(date_field)
        elif period == 'week':
            trunc_func = TruncWeek(date_field)
        elif period == 'month':
            trunc_func = TruncMonth(date_field)
        else:
            trunc_func = TruncDay(date_field)
            
        # Préparer l'agrégation
        if value_field:
            # Agréger la somme du champ spécifié
            aggregation = Sum(value_field)
        else:
            # Compter les occurrences
            aggregation = Count('id')
            
        # Effectuer l'agrégation
        if group_by:
            # Grouper par période et par le champ spécifié
            data = queryset.annotate(
                period=trunc_func
            ).values('period', group_by).annotate(
                value=aggregation
            ).order_by('period', group_by)
            
            # Formater les résultats
            result = {}
            for entry in data:
                group = entry[group_by]
                if group not in result:
                    result[group] = []
                    
                result[group].append({
                    'date': entry['period'].isoformat() if entry['period'] else None,
                    'value': entry['value']
                })
                
            return result
        else:
            # Grouper uniquement par période
            data = queryset.annotate(
                period=trunc_func
            ).values('period').annotate(
                value=aggregation
            ).order_by('period')
            
            # Formater les résultats
            result = []
            for entry in data:
                result.append({
                    'date': entry['period'].isoformat() if entry['period'] else None,
                    'value': entry['value']
                })
                
            return result
    
    @staticmethod
    def get_quality_trends(farm_id=None, start_date=None, end_date=None, period='week'):
        """
        Génère des tendances de qualité des prunes au fil du temps.
        
        Args:
            farm_id: ID de la ferme optionnel pour filtrer les données
            start_date: Date de début optionnelle
            end_date: Date de fin optionnelle
            period: Période d'agrégation ('day', 'week', 'month')
            
        Returns:
            dict: Tendances de qualité par catégorie
        """
        # Préparer le queryset de base
        queryset = PlumClassification.objects.all()
        
        # Filtrer par ferme si spécifié
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
            
        # Obtenir les données de séries temporelles par classe
        return DashboardAnalytics.get_time_series_data(
            queryset=queryset,
            date_field='created_at',
            period=period,
            group_by='class_name',
            start_date=start_date,
            end_date=end_date
        )
    
    @staticmethod
    def get_farm_comparison(user_id=None, metric='quality_score'):
        """
        Compare les performances des fermes selon une métrique spécifiée.
        
        Args:
            user_id: ID de l'utilisateur optionnel pour filtrer les fermes
            metric: Métrique à comparer ('quality_score', 'volume', 'efficiency')
            
        Returns:
            list: Données de comparaison des fermes
        """
        # Filtrer les fermes si un utilisateur est spécifié
        farms = Farm.objects.all()
        if user_id:
            farms = farms.filter(owner_id=user_id)
            
        result = []
        
        for farm in farms:
            # Récupérer les classifications pour cette ferme
            farm_classifications = PlumClassification.objects.filter(farm=farm)
            
            # Calculer les métriques
            total_classifications = farm_classifications.count()
            
            if total_classifications == 0:
                continue
                
            # Calculer le score de qualité (pourcentage de "bonne_qualite")
            good_quality_count = farm_classifications.filter(class_name='bonne_qualite').count()
            quality_score = (good_quality_count / total_classifications) * 100 if total_classifications > 0 else 0
            
            # Calculer l'efficacité (confiance moyenne)
            avg_confidence = farm_classifications.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
            
            # Ajouter les données à la liste de résultats
            farm_data = {
                'id': farm.id,
                'name': farm.name,
                'location': farm.location,
                'total_classifications': total_classifications,
                'quality_score': round(quality_score, 2),
                'efficiency': round(avg_confidence * 100, 2),
                'volume': total_classifications  # Utiliser le nombre de classifications comme proxy du volume
            }
            
            result.append(farm_data)
            
        # Trier selon la métrique spécifiée
        if result:
            result.sort(key=lambda x: x.get(metric, 0), reverse=True)
            
        return result
    
    @staticmethod
    def predict_quality_distribution(farm_id=None, days_ahead=7):
        """
        Prédit la distribution de qualité future basée sur les tendances historiques.
        Utilise une méthode simple de moyenne mobile.
        
        Args:
            farm_id: ID de la ferme optionnel
            days_ahead: Nombre de jours à prédire
            
        Returns:
            dict: Prédiction de distribution de qualité
        """
        # Récupérer les classifications
        queryset = PlumClassification.objects.all()
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
            
        # Récupérer les données des 30 derniers jours
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_data = queryset.filter(created_at__gte=thirty_days_ago)
        
        # Compter les occurrences par classe
        class_counts = {}
        total = recent_data.count()
        
        if total == 0:
            return {
                'prediction_date': (timezone.now() + timedelta(days=days_ahead)).isoformat(),
                'predicted_distribution': {},
                'confidence': 0,
                'method': 'moving_average'
            }
            
        for classification in recent_data:
            class_name = classification.class_name
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
        # Calculer les pourcentages
        class_percentages = {}
        for class_name, count in class_counts.items():
            percentage = (count / total) * 100
            class_percentages[class_name] = round(percentage, 2)
            
        # Pour une prédiction simple, nous utilisons la distribution actuelle
        # Une implémentation plus avancée utiliserait des séries temporelles ou du ML
        
        return {
            'prediction_date': (timezone.now() + timedelta(days=days_ahead)).isoformat(),
            'predicted_distribution': class_percentages,
            'confidence': min(total / 100, 0.95),  # Confiance basée sur la taille de l'échantillon, max 95%
            'method': 'moving_average'
        }
    
    @staticmethod
    def get_user_activity_heatmap(days=30):
        """
        Génère un heatmap d'activité utilisateur par jour et heure.
        
        Args:
            days: Nombre de jours d'historique à inclure
            
        Returns:
            dict: Données de heatmap d'activité
        """
        # Récupérer les classifications récentes
        start_date = timezone.now() - timedelta(days=days)
        classifications = PlumClassification.objects.filter(created_at__gte=start_date)
        
        # Initialiser la matrice de heatmap (jours de la semaine x heures)
        heatmap = [[0 for _ in range(24)] for _ in range(7)]
        
        # Remplir la matrice
        for classification in classifications:
            day_of_week = classification.created_at.weekday()  # 0-6 (lundi-dimanche)
            hour_of_day = classification.created_at.hour  # 0-23
            
            heatmap[day_of_week][hour_of_day] += 1
            
        # Formater les résultats
        days_labels = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        hours_labels = [f"{h}h" for h in range(24)]
        
        result = {
            'data': heatmap,
            'days': days_labels,
            'hours': hours_labels,
            'max_value': max([max(row) for row in heatmap]) if heatmap else 0
        }
        
        return result
    
    @staticmethod
    def get_classification_accuracy_metrics(model_version_id=None):
        """
        Calcule des métriques d'exactitude pour les classifications.
        
        Args:
            model_version_id: ID de version du modèle optionnel
            
        Returns:
            dict: Métriques d'exactitude
        """
        # Récupérer les classifications
        queryset = PlumClassification.objects.all()
        
        # Filtrer par version du modèle si spécifié
        if model_version_id:
            # Cette fonctionnalité nécessiterait d'ajouter un champ model_version à PlumClassification
            pass
            
        # Calculer la confiance moyenne globale
        avg_confidence = queryset.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
        
        # Calculer la confiance moyenne par classe
        confidence_by_class = {}
        
        class_choices = dict(PlumClassification.CLASS_CHOICES)
        
        for class_key, class_name in class_choices.items():
            class_queryset = queryset.filter(class_name=class_key)
            class_avg = class_queryset.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
            confidence_by_class[class_name] = round(class_avg, 4)
            
        # Calculer la distribution des scores de confiance
        confidence_distribution = {
            '0.9-1.0': queryset.filter(confidence_score__gte=0.9).count(),
            '0.8-0.9': queryset.filter(confidence_score__gte=0.8, confidence_score__lt=0.9).count(),
            '0.7-0.8': queryset.filter(confidence_score__gte=0.7, confidence_score__lt=0.8).count(),
            '0.6-0.7': queryset.filter(confidence_score__gte=0.6, confidence_score__lt=0.7).count(),
            '0.5-0.6': queryset.filter(confidence_score__gte=0.5, confidence_score__lt=0.6).count(),
            '0.0-0.5': queryset.filter(confidence_score__lt=0.5).count(),
        }
        
        return {
            'average_confidence': round(avg_confidence, 4),
            'confidence_by_class': confidence_by_class,
            'confidence_distribution': confidence_distribution,
            'total_classifications': queryset.count()
        }
