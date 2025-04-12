import unittest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import os
import tempfile
from PIL import Image
import numpy as np

from users.models import Farm
from plum_classifier.models import PlumBatch, PlumClassification, ModelVersion
from plum_classifier.services import PlumClassifierService

User = get_user_model()

class UserModelTests(TestCase):
    """Tests pour le modèle utilisateur personnalisé."""
    
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'farmer'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_user_creation(self):
        """Teste la création d'un utilisateur."""
        self.assertEqual(self.user.username, self.user_data['username'])
        self.assertEqual(self.user.email, self.user_data['email'])
        self.assertEqual(self.user.first_name, self.user_data['first_name'])
        self.assertEqual(self.user.last_name, self.user_data['last_name'])
        self.assertEqual(self.user.role, self.user_data['role'])
        self.assertFalse(self.user.email_verified)
        self.assertTrue(self.user.check_password(self.user_data['password']))
    
    def test_user_properties(self):
        """Teste les propriétés du modèle utilisateur."""
        self.assertTrue(self.user.is_farmer)
        self.assertFalse(self.user.is_technician)
        self.assertFalse(self.user.is_admin_user)
        self.assertEqual(self.user.full_name, f"{self.user_data['first_name']} {self.user_data['last_name']}")
    
    def test_email_verification_token(self):
        """Teste la génération du token de vérification d'email."""
        token = self.user.generate_email_verification_token()
        self.assertIsNotNone(token)
        self.assertEqual(token, self.user.email_verification_token)


class FarmModelTests(TestCase):
    """Tests pour le modèle Farm."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='farmowner',
            email='farmer@example.com',
            password='securepassword123',
            role='farmer'
        )
        self.farm_data = {
            'name': 'Test Farm',
            'location': 'Test Location',
            'size': 10.5,
            'owner': self.user,
            'description': 'A test farm',
            'latitude': 45.123456,
            'longitude': 5.123456
        }
        self.farm = Farm.objects.create(**self.farm_data)
    
    def test_farm_creation(self):
        """Teste la création d'une ferme."""
        self.assertEqual(self.farm.name, self.farm_data['name'])
        self.assertEqual(self.farm.location, self.farm_data['location'])
        self.assertEqual(self.farm.size, self.farm_data['size'])
        self.assertEqual(self.farm.owner, self.user)
        self.assertEqual(self.farm.description, self.farm_data['description'])
        self.assertEqual(self.farm.latitude, self.farm_data['latitude'])
        self.assertEqual(self.farm.longitude, self.farm_data['longitude'])
    
    def test_farm_string_representation(self):
        """Teste la représentation en chaîne de caractères d'une ferme."""
        self.assertEqual(str(self.farm), self.farm_data['name'])


class PlumBatchModelTests(TestCase):
    """Tests pour le modèle PlumBatch."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='batchcreator',
            email='creator@example.com',
            password='securepassword123',
            role='farmer'
        )
        self.farm = Farm.objects.create(
            name='Batch Farm',
            location='Batch Location',
            owner=self.user
        )
        self.batch_data = {
            'name': 'Test Batch',
            'description': 'A test batch of plums',
            'farm': self.farm,
            'created_by': self.user,
            'status': 'pending'
        }
        self.batch = PlumBatch.objects.create(**self.batch_data)
    
    def test_batch_creation(self):
        """Teste la création d'un lot de prunes."""
        self.assertEqual(self.batch.name, self.batch_data['name'])
        self.assertEqual(self.batch.description, self.batch_data['description'])
        self.assertEqual(self.batch.farm, self.farm)
        self.assertEqual(self.batch.created_by, self.user)
        self.assertEqual(self.batch.status, self.batch_data['status'])
        self.assertEqual(self.batch.total_plums, 0)
        self.assertEqual(self.batch.quality_distribution, {})
    
    def test_batch_string_representation(self):
        """Teste la représentation en chaîne de caractères d'un lot."""
        self.assertEqual(str(self.batch), f"{self.batch_data['name']} - {self.farm.name}")
    
    def test_update_classification_summary(self):
        """Teste la mise à jour du résumé de classification."""
        # Créer quelques classifications
        for i, class_name in enumerate(['bonne_qualite', 'non_mure', 'tachetee']):
            PlumClassification.objects.create(
                image_path=f'/path/to/image_{i}.jpg',
                uploaded_by=self.user,
                farm=self.farm,
                batch=self.batch,
                class_name=class_name,
                confidence_score=0.8 + i * 0.05,
                is_plum=True
            )
        
        # Mettre à jour le résumé
        self.batch.update_classification_summary()
        
        # Vérifier les résultats
        self.assertEqual(self.batch.total_plums, 3)
        self.assertEqual(self.batch.status, 'classified')
        self.assertEqual(len(self.batch.quality_distribution), 3)
        
        # Vérifier les pourcentages
        for class_name in ['bonne_qualite', 'non_mure', 'tachetee']:
            self.assertIn(class_name, self.batch.quality_distribution)
            self.assertEqual(self.batch.quality_distribution[class_name]['count'], 1)
            self.assertEqual(self.batch.quality_distribution[class_name]['percentage'], 33.33)


class AuthenticationAPITests(APITestCase):
    """Tests pour les endpoints d'authentification de l'API."""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.token_url = reverse('token_obtain_pair')
        self.user_data = {
            'username': 'apiuser',
            'email': 'apiuser@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'first_name': 'API',
            'last_name': 'User',
            'role': 'farmer'
        }
    
    def test_user_registration(self):
        """Teste l'enregistrement d'un utilisateur via l'API."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, self.user_data['username'])
        self.assertFalse(User.objects.get().is_active)  # L'utilisateur est inactif jusqu'à la vérification de l'email
    
    def test_user_login_without_verification(self):
        """Teste la tentative de connexion sans vérification d'email."""
        # Créer un utilisateur
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            role=self.user_data['role'],
            is_active=True  # L'utilisateur est actif mais l'email n'est pas vérifié
        )
        
        # Tenter de se connecter
        response = self.client.post(self.token_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')
        
        # La connexion doit échouer car l'email n'est pas vérifié
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_login_with_verification(self):
        """Teste la connexion avec vérification d'email."""
        # Créer un utilisateur avec email vérifié
        user = User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            role=self.user_data['role'],
            is_active=True,
            email_verified=True
        )
        
        # Se connecter
        response = self.client.post(self.token_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')
        
        # La connexion doit réussir
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class PlumClassifierServiceTests(unittest.TestCase):
    """Tests pour le service de classification des prunes."""
    
    def setUp(self):
        self.service = PlumClassifierService.get_instance()
        
        # Créer une image de test
        self.test_image_path = os.path.join(tempfile.gettempdir(), 'test_plum.jpg')
        img = Image.new('RGB', (320, 320), color=(73, 109, 137))
        img.save(self.test_image_path)
    
    def tearDown(self):
        # Supprimer l'image de test
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def test_singleton_pattern(self):
        """Teste que le service est bien un singleton."""
        service2 = PlumClassifierService.get_instance()
        self.assertIs(self.service, service2)
    
    def test_model_loading_without_model_file(self):
        """Teste le comportement lorsqu'aucun modèle n'est disponible."""
        # Réinitialiser l'état du service
        self.service.model = None
        self.service.model_loaded = False
        
        # Le chargement doit échouer car aucun modèle n'est disponible
        result = self.service.lazy_load_model()
        self.assertFalse(result)
    
    def test_classification_without_model(self):
        """Teste la classification sans modèle chargé."""
        # Réinitialiser l'état du service
        self.service.model = None
        self.service.model_loaded = False
        
        # La classification doit retourner une erreur
        result = self.service.classify_image(self.test_image_path)
        self.assertIn('error', result)
        self.assertEqual(result['class_name'], 'unknown')
        self.assertEqual(result['confidence'], 0.0)
        self.assertFalse(result['est_prune'])
        self.assertIn('processing_time', result)


class PlumClassificationAPITests(APITestCase):
    """Tests pour les endpoints de classification de l'API."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='classificationuser',
            email='classifier@example.com',
            password='securepassword123',
            role='farmer',
            is_active=True,
            email_verified=True
        )
        
        # Créer une ferme
        self.farm = Farm.objects.create(
            name='Classification Farm',
            location='Classification Location',
            owner=self.user
        )
        
        # Créer un lot
        self.batch = PlumBatch.objects.create(
            name='Classification Batch',
            farm=self.farm,
            created_by=self.user
        )
        
        # Créer une image de test
        self.test_image_path = os.path.join(tempfile.gettempdir(), 'test_plum.jpg')
        img = Image.new('RGB', (320, 320), color=(73, 109, 137))
        img.save(self.test_image_path)
        
        # URL pour la classification
        self.classify_url = reverse('classification-classify')
        
        # Authentifier l'utilisateur
        self.client.force_authenticate(user=self.user)
    
    def tearDown(self):
        # Supprimer l'image de test
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def test_classify_endpoint_without_image(self):
        """Teste l'endpoint de classification sans image."""
        response = self.client.post(self.classify_url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_classify_endpoint_with_image(self):
        """Teste l'endpoint de classification avec une image."""
        # Note: Ce test ne fonctionnera pas complètement sans un modèle réel
        # Nous testons seulement la partie API, pas la classification elle-même
        
        with open(self.test_image_path, 'rb') as img:
            response = self.client.post(
                self.classify_url,
                {
                    'image': img,
                    'farm_id': self.farm.id,
                    'batch_id': self.batch.id
                },
                format='multipart'
            )
        
        # La réponse peut être 201 (succès) ou 500 (erreur de modèle)
        # Dans un environnement de test sans modèle, nous nous attendons à une erreur 500
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        if response.status_code == status.HTTP_201_CREATED:
            # Si la classification a réussi, vérifier les données de réponse
            self.assertIn('id', response.data)
            self.assertIn('class_name', response.data)
            self.assertIn('confidence_score', response.data)
            self.assertIn('is_plum', response.data)
        else:
            # Si la classification a échoué, vérifier le message d'erreur
            self.assertIn('error', response.data)


if __name__ == '__main__':
    unittest.main()
