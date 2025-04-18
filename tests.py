import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.conf import settings
import os
import json

from users.models import Farm
from plum_classifier.models import PlumBatch, PlumClassification
from dashboard.models import DashboardPreference
from api.optimizations import query_debugger, cached_queryset, optimize_queryset
from api.security import FileSecurity, InputValidation
from api.utils import ResponseBuilder, ServiceBase

User = get_user_model()

class SecurityTests(TestCase):
    """Tests pour les fonctionnalités de sécurité."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            role='farmer'
        )
        
        # Créer une ferme de test
        self.farm = Farm.objects.create(
            name='Test Farm',
            location='Test Location',
            owner=self.user
        )
    
    def test_env_variables(self):
        """Teste que les variables d'environnement sensibles ne sont pas en dur dans le code."""
        # Vérifier que la chaîne de connexion à la base de données n'est pas en dur
        self.assertNotIn('postgresql://plum_user:', str(settings.DATABASES))
        
        # Vérifier que SECRET_KEY utilise une variable d'environnement
        self.assertNotEqual(settings.SECRET_KEY, 'django-insecure-default-key-for-development-only')
    
    def test_cors_settings(self):
        """Teste que les paramètres CORS sont correctement configurés."""
        # En mode DEBUG, CORS_ALLOW_ALL_ORIGINS devrait être True
        if settings.DEBUG:
            self.assertTrue(settings.CORS_ALLOW_ALL_ORIGINS)
        # En production, CORS_ALLOW_ALL_ORIGINS devrait être False
        else:
            self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)
            self.assertTrue(hasattr(settings, 'CORS_ALLOWED_ORIGINS'))
    
    def test_file_security_validation(self):
        """Teste les fonctions de validation de sécurité des fichiers."""
        # Créer un fichier de test
        test_file_path = os.path.join(settings.MEDIA_ROOT, 'test_image.jpg')
        with open(test_file_path, 'w') as f:
            f.write('test content')
        
        # Tester la validation de taille de fichier
        with open(test_file_path, 'rb') as f:
            file_obj = type('MockFile', (), {'size': 1024 * 1024 * 10, 'name': 'test.jpg'})()
            with self.assertRaises(Exception):
                FileSecurity.validate_file_size(file_obj, 1024 * 1024 * 5)  # 5MB
        
        # Nettoyer
        os.remove(test_file_path)
    
    def test_input_validation(self):
        """Teste les fonctions de validation des entrées utilisateur."""
        # Tester la validation des coordonnées
        with self.assertRaises(Exception):
            InputValidation.validate_coordinates(100, 50)  # Latitude invalide
        
        with self.assertRaises(Exception):
            InputValidation.validate_coordinates(50, 200)  # Longitude invalide
        
        # Tester la validation réussie
        self.assertTrue(InputValidation.validate_coordinates(45, 90))


class PerformanceTests(TestCase):
    """Tests pour les optimisations de performance."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            role='farmer'
        )
        
        # Créer une ferme de test
        self.farm = Farm.objects.create(
            name='Test Farm',
            location='Test Location',
            owner=self.user
        )
    
    @query_debugger
    def test_query_debugger(self):
        """Teste le décorateur query_debugger."""
        # Cette fonction est décorée avec @query_debugger
        # Le test vérifie simplement que le décorateur ne cause pas d'erreur
        farms = Farm.objects.all()
        self.assertGreaterEqual(farms.count(), 1)
    
    def test_optimize_queryset(self):
        """Teste la fonction optimize_queryset."""
        # Créer quelques objets pour le test
        batch = PlumBatch.objects.create(
            name='Test Batch',
            farm=self.farm,
            created_by=self.user
        )
        
        # Tester l'optimisation du queryset
        queryset = PlumBatch.objects.all()
        optimized = optimize_queryset(queryset, select_related=['farm', 'created_by'])
        
        # Vérifier que le queryset est bien optimisé
        self.assertEqual(optimized.query.select_related, {'farm': {}, 'created_by': {}})


class DashboardTests(APITestCase):
    """Tests pour les fonctionnalités du dashboard."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
            role='farmer'
        )
        
        # Créer une ferme de test
        self.farm = Farm.objects.create(
            name='Test Farm',
            location='Test Location',
            owner=self.user
        )
        
        # Authentifier le client API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_dashboard_preferences(self):
        """Teste les préférences du dashboard."""
        # Vérifier que les préférences par défaut sont créées
        response = self.client.get(reverse('dashboard-preferences-my-preferences'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que les préférences contiennent les champs attendus
        self.assertIn('layout', response.data)
        self.assertIn('visible_metrics', response.data)
        
        # Mettre à jour les préférences
        new_prefs = {
            'layout': {'columns': 2},
            'visible_metrics': ['total_classifications', 'average_confidence'],
            'refresh_interval': 600
        }
        response = self.client.put(reverse('dashboard-preferences-update-preferences'), new_prefs)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que les préférences ont été mises à jour
        response = self.client.get(reverse('dashboard-preferences-my-preferences'))
        self.assertEqual(response.data['refresh_interval'], 600)
    
    def test_user_dashboard(self):
        """Teste l'endpoint du dashboard utilisateur."""
        response = self.client.get(reverse('user-dashboard'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que la réponse contient les données attendues pour un agriculteur
        self.assertIn('farms', response.data)
        self.assertIn('total_classifications', response.data)
        self.assertIn('average_confidence', response.data)


class UtilsTests(TestCase):
    """Tests pour les utilitaires."""
    
    def test_response_builder(self):
        """Teste la classe ResponseBuilder."""
        # Tester la réponse de succès
        success_response = ResponseBuilder.success(data={'test': 'data'}, message='Success')
        self.assertEqual(success_response.status_code, status.HTTP_200_OK)
        self.assertEqual(success_response.data['success'], True)
        self.assertEqual(success_response.data['message'], 'Success')
        self.assertEqual(success_response.data['data'], {'test': 'data'})
        
        # Tester la réponse d'erreur
        error_response = ResponseBuilder.error(message='Error', errors={'field': 'Invalid'})
        self.assertEqual(error_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(error_response.data['success'], False)
        self.assertEqual(error_response.data['message'], 'Error')
        self.assertEqual(error_response.data['errors'], {'field': 'Invalid'})
    
    def test_service_base(self):
        """Teste la classe ServiceBase."""
        # Créer une classe de service de test
        class TestService(ServiceBase):
            def process(self):
                return self.value * 2
        
        # Tester l'exécution du service
        result = TestService.execute(value=5)
        self.assertEqual(result, 10)


if __name__ == '__main__':
    unittest.main()
