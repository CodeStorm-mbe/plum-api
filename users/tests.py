from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Farm, UserSettings
import uuid

User = get_user_model()

class UserModelTests(TestCase):
    """Tests pour le modèle User."""
    
    def test_create_user(self):
        """Test de création d'un utilisateur standard."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpassword123"))
        self.assertEqual(user.role, User.Roles.FARMER)
        self.assertFalse(user.email_verified)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
    def test_create_superuser(self):
        """Test de création d'un superutilisateur."""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123"
        )
        self.assertEqual(admin.username, "admin")
        self.assertEqual(admin.email, "admin@example.com")
        self.assertTrue(admin.check_password("adminpassword123"))
        self.assertEqual(admin.role, User.Roles.ADMIN)
        self.assertTrue(admin.email_verified)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        
    def test_user_settings_creation(self):
        """Test que les paramètres utilisateur sont créés automatiquement."""
        user = User.objects.create_user(
            username="settingsuser",
            email="settings@example.com",
            password="password123"
        )
        self.assertTrue(hasattr(user, 'settings'))
        self.assertIsInstance(user.settings, UserSettings)
        
    def test_email_verification_token(self):
        """Test de génération du token de vérification d'email."""
        user = User.objects.create_user(
            username="verifyuser",
            email="verify@example.com",
            password="password123"
        )
        token = user.generate_email_verification_token()
        self.assertIsNotNone(token)
        self.assertEqual(token, user.email_verification_token)
        self.assertIsNotNone(user.email_verification_sent_at)


class FarmModelTests(TestCase):
    """Tests pour le modèle Farm."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="farmowner",
            email="farmer@example.com",
            password="password123"
        )
        
    def test_create_farm(self):
        """Test de création d'une ferme."""
        farm = Farm.objects.create(
            name="Test Farm",
            location="Test Location",
            size=10.5,
            owner=self.user,
            description="A test farm",
            latitude=45.5,
            longitude=-73.5
        )
        self.assertEqual(farm.name, "Test Farm")
        self.assertEqual(farm.location, "Test Location")
        self.assertEqual(float(farm.size), 10.5)
        self.assertEqual(farm.owner, self.user)
        self.assertEqual(farm.description, "A test farm")
        self.assertEqual(float(farm.latitude), 45.5)
        self.assertEqual(float(farm.longitude), -73.5)
        
    def test_farm_coordinates(self):
        """Test de la propriété coordinates."""
        farm = Farm.objects.create(
            name="Coordinates Farm",
            location="Somewhere",
            owner=self.user,
            latitude=45.5,
            longitude=-73.5
        )
        self.assertEqual(farm.coordinates, (45.5, -73.5))
        
    def test_farm_has_location_data(self):
        """Test de la propriété has_location_data."""
        farm1 = Farm.objects.create(
            name="Located Farm",
            location="Somewhere",
            owner=self.user,
            latitude=45.5,
            longitude=-73.5
        )
        farm2 = Farm.objects.create(
            name="Unlocated Farm",
            location="Somewhere else",
            owner=self.user
        )
        self.assertTrue(farm1.has_location_data)
        self.assertFalse(farm2.has_location_data)


class UserAPITests(APITestCase):
    """Tests pour l'API des utilisateurs."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.user.email_verified = True
        self.user.save()
        
    def test_user_list(self):
        """Test de la liste des utilisateurs (admin seulement)."""
        # Non authentifié
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Utilisateur normal
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # admin + testuser
        
    def test_user_detail(self):
        """Test des détails d'un utilisateur."""
        # Non authentifié
        response = self.client.get(reverse('user-detail', args=[str(self.user.id)]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Utilisateur accédant à son propre profil
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-detail', args=[str(self.user.id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
        # Utilisateur essayant d'accéder au profil d'un autre
        response = self.client.get(reverse('user-detail', args=[str(self.admin.id)]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin accédant au profil d'un autre
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('user-detail', args=[str(self.user.id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        
    def test_me_endpoint(self):
        """Test de l'endpoint 'me'."""
        # Non authentifié
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Utilisateur authentifié
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        
    def test_settings_endpoint(self):
        """Test de l'endpoint 'settings'."""
        # Non authentifié
        response = self.client.get(reverse('user-settings'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Utilisateur authentifié
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-settings'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Mise à jour des paramètres
        new_settings = {
            'language': 'en',
            'notification_preferences': {'email': True, 'push': False, 'sms': False},
            'ui_preferences': {'theme': 'dark', 'dashboard_layout': 'grid', 'items_per_page': 20}
        }
        response = self.client.patch(reverse('user-settings'), new_settings, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['language'], 'en')
        self.assertEqual(response.data['notification_preferences']['email'], True)
        self.assertEqual(response.data['ui_preferences']['theme'], 'dark')


class FarmAPITests(APITestCase):
    """Tests pour l'API des fermes."""
    
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword123"
        )
        self.user1 = User.objects.create_user(
            username="farmer1",
            email="farmer1@example.com",
            password="password123",
            role=User.Roles.FARMER
        )
        self.user1.email_verified = True
        self.user1.save()
        
        self.user2 = User.objects.create_user(
            username="farmer2",
            email="farmer2@example.com",
            password="password123",
            role=User.Roles.FARMER
        )
        self.user2.email_verified = True
        self.user2.save()
        
        self.farm1 = Farm.objects.create(
            name="Farm 1",
            location="Location 1",
            size=10.5,
            owner=self.user1,
            description="First test farm",
            latitude=45.5,
            longitude=-73.5
        )
        
        self.farm2 = Farm.objects.create(
            name="Farm 2",
            location="Location 2",
            size=20.0,
            owner=self.user2,
            description="Second test farm"
        )
        
    def test_farm_list(self):
        """Test de la liste des fermes."""
        # Non authentifié
        response = self.client.get(reverse('farm-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Utilisateur 1 ne voit que ses propres fermes
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('farm-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Farm 1')
        
        # Admin voit toutes les fermes
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('farm-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_farm_detail(self):
        """Test des détails d'une ferme."""
        # Non authentifié
        response = self.client.get(reverse('farm-detail', args=[str(self.farm1.id)]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Propriétaire de la ferme
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('farm-detail', args=[str(self.farm1.id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Farm 1')
        
        # Non-propriétaire essayant d'accéder à une ferme
        response = self.client.get(reverse('farm-detail', args=[str(self.farm2.id)]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Filtré par queryset
        
        # Admin accédant à n'importe quelle ferme
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('farm-detail', args=[str(self.farm2.id)]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Farm 2')
        
    def test_create_farm(self):
        """Test de création d'une ferme."""
        self.client.force_authenticate(user=self.user1)
        new_farm_data = {
            'name': 'New Farm',
            'location': 'New Location',
            'size': 15.0,
            'description': 'A new test farm',
            'latitude': 46.0,
            'longitude': -74.0
        }
        response = self.client.post(reverse('farm-list'), new_farm_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Farm')
        self.assertEqual(response.data['owner_username'], 'farmer1')
        
        # Vérifier que la ferme a bien été créée en base
        self.assertEqual(Farm.objects.filter(name='New Farm').count(), 1)
        
    def test_update_farm(self):
        """Test de mise à jour d'une ferme."""
        self.client.force_authenticate(user=self.user1)
        update_data = {
            'name': 'Updated Farm 1',
            'description': 'Updated description'
        }
        response = self.client.patch(reverse('farm-detail', args=[str(self.farm1.id)]), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Farm 1')
        self.assertEqual(response.data['description'], 'Updated description')
        
        # Vérifier que les autres champs n'ont pas été modifiés
        self.assertEqual(float(response.data['size']), 10.5)
        
    def test_delete_farm(self):
        """Test de suppression d'une ferme."""
        # Non-propriétaire essayant de supprimer une ferme
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(reverse('farm-detail', args=[str(self.farm1.id)]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Filtré par queryset
        
        # Propriétaire supprimant sa ferme
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(reverse('farm-detail', args=[str(self.farm1.id)]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que la ferme a bien été supprimée
        self.assertEqual(Farm.objects.filter(id=self.farm1.id).count(), 0)
