# Documentation du Système de Classification des Prunes

## Vue d'ensemble

Le Système de Classification des Prunes est une API backend Django conçue pour aider les agriculteurs à classifier automatiquement leurs prunes en utilisant un modèle de machine learning. Cette solution permet aux agriculteurs de prendre des photos de leurs prunes et d'obtenir instantanément une classification de qualité, facilitant ainsi leurs décisions de récolte et de commercialisation.

## Fonctionnalités principales

- **Classification d'images** : Analyse des images de prunes pour déterminer leur qualité
- **Gestion des lots** : Organisation des prunes en lots pour un traitement par groupe
- **Statistiques détaillées** : Visualisation des distributions de qualité et des tendances
- **Gestion des fermes** : Suivi des classifications par ferme
- **Authentification sécurisée** : Système d'authentification avec vérification d'email
- **Interface d'administration** : Tableau de bord intuitif pour la gestion des données
- **API REST** : Endpoints pour l'intégration avec des applications mobiles ou web

## Architecture technique

Le système est construit avec les technologies suivantes :

- **Backend** : Django 5.2 avec Django REST Framework
- **Authentification** : JWT (JSON Web Tokens)
- **Base de données** : SQLite (développement) / PostgreSQL (production)
- **Modèle ML** : PyTorch (fichier .pt à ajouter séparément)
- **Cache** : Redis
- **Tâches asynchrones** : Celery
- **Documentation API** : Swagger/OpenAPI

## Structure du projet

```
plum_api/
├── plum_project/         # Configuration principale du projet
├── users/                # Gestion des utilisateurs et des fermes
├── authentication/       # Système d'authentification avec vérification d'email
├── plum_classifier/      # Logique de classification des prunes
├── api/                  # Points d'entrée API REST
├── dashboard/            # Interface d'administration
├── media/                # Stockage des images téléchargées
├── models/               # Stockage des modèles de machine learning
├── static/               # Fichiers statiques
├── templates/            # Templates HTML
└── venv/                 # Environnement virtuel Python
```

## Installation

### Prérequis

- Python 3.10+
- pip
- virtualenv
- Redis (pour le cache et Celery)

### Étapes d'installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/votre-organisation/plum-classification-api.git
   cd plum-classification-api
   ```

2. Créer et activer un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurer les variables d'environnement :
   ```bash
   cp .env.example .env
   # Modifier le fichier .env avec vos paramètres
   ```

5. Appliquer les migrations :
   ```bash
   python manage.py migrate
   ```

6. Créer un superutilisateur :
   ```bash
   python manage.py createsuperuser
   ```

7. Ajouter le modèle de classification :
   - Placer votre fichier de modèle PyTorch (.pt) dans le répertoire `models/`
   - Placer le fichier de métadonnées associé (.json) dans le même répertoire

8. Démarrer le serveur :
   ```bash
   python manage.py runserver
   ```

## Configuration

### Variables d'environnement

Le fichier `.env` doit contenir les variables suivantes :

```
# Django
SECRET_KEY=votre-clé-secrète
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
# Pour PostgreSQL :
# DB_ENGINE=django.db.backends.postgresql
# DB_NAME=plum_db
# DB_USER=postgres
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Pour SMTP :
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre-email@gmail.com
# EMAIL_HOST_PASSWORD=votre-mot-de-passe
DEFAULT_FROM_EMAIL=noreply@plumclassifier.com

# Frontend
FRONTEND_URL=http://localhost:3000

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Configuration du modèle

Le système recherche automatiquement un fichier de modèle PyTorch (.pt) dans le répertoire `models/`. Si un fichier de métadonnées associé (.json) est présent, il sera utilisé pour configurer le modèle. Sinon, des valeurs par défaut seront utilisées.

Format du fichier de métadonnées :

```json
{
  "model_name": "efficientnet_b4",
  "version": "1.0.0",
  "num_classes": 6,
  "confidence_threshold": 0.7,
  "input_shape": [1, 3, 320, 320],
  "idx_to_class": {
    "0": "bonne_qualite",
    "1": "non_mure",
    "2": "tachetee",
    "3": "fissuree",
    "4": "meurtrie",
    "5": "pourrie"
  },
  "accuracy": 0.92,
  "f1_score": 0.91,
  "precision": 0.90,
  "recall": 0.89,
  "training_date": "2025-03-15T12:00:00Z",
  "training_duration": 5.2,
  "dataset_size": 10000
}
```

## Utilisation de l'API

### Authentification

1. **Inscription** :
   ```
   POST /api/auth/register/
   ```
   Corps de la requête :
   ```json
   {
     "username": "agriculteur1",
     "email": "agriculteur1@example.com",
     "password": "motdepasse123",
     "confirm_password": "motdepasse123",
     "first_name": "Jean",
     "last_name": "Dupont",
     "role": "farmer",
     "phone_number": "+33612345678"
   }
   ```

2. **Vérification de l'email** :
   ```
   POST /api/auth/verify-email/
   ```
   Corps de la requête :
   ```json
   {
     "token": "token-de-verification-recu-par-email"
   }
   ```

3. **Connexion** :
   ```
   POST /api/auth/token/
   ```
   Corps de la requête :
   ```json
   {
     "username": "agriculteur1",
     "password": "motdepasse123"
   }
   ```
   Réponse :
   ```json
   {
     "access": "token-jwt-access",
     "refresh": "token-jwt-refresh",
     "user_id": 1,
     "username": "agriculteur1",
     "email": "agriculteur1@example.com",
     "role": "farmer"
   }
   ```

4. **Rafraîchissement du token** :
   ```
   POST /api/auth/token/refresh/
   ```
   Corps de la requête :
   ```json
   {
     "refresh": "token-jwt-refresh"
   }
   ```

### Gestion des fermes

1. **Créer une ferme** :
   ```
   POST /api/farms/
   ```
   Corps de la requête :
   ```json
   {
     "name": "Ma Ferme",
     "location": "Région Sud",
     "size": 15.5,
     "description": "Ferme de prunes biologiques",
     "latitude": 45.123456,
     "longitude": 5.123456
   }
   ```

2. **Obtenir les fermes** :
   ```
   GET /api/farms/
   ```

3. **Obtenir les statistiques d'une ferme** :
   ```
   GET /api/farms/{id}/stats/
   ```

### Classification des prunes

1. **Classifier une image** :
   ```
   POST /api/classifications/classify/
   ```
   Corps de la requête (multipart/form-data) :
   ```
   image: [fichier image]
   farm_id: 1
   batch_id: 1 (optionnel)
   use_tta: false (optionnel)
   ```
   Réponse :
   ```json
   {
     "id": 1,
     "image_path": "/media/plum_images/abc123.jpg",
     "class_name": "bonne_qualite",
     "class_name_display": "Bonne qualité",
     "confidence_score": 0.95,
     "is_plum": true,
     "processing_time": 0.25,
     "created_at": "2025-04-12T15:30:45Z"
   }
   ```

2. **Obtenir l'historique des classifications** :
   ```
   GET /api/classifications/
   ```

3. **Obtenir les statistiques des classifications** :
   ```
   GET /api/classifications/stats/?start_date=2025-01-01&end_date=2025-12-31
   ```

### Gestion des lots

1. **Créer un lot** :
   ```
   POST /api/batches/
   ```
   Corps de la requête :
   ```json
   {
     "name": "Lot du 12 avril",
     "description": "Prunes récoltées le 12 avril",
     "farm": 1
   }
   ```

2. **Classifier un lot d'images** :
   ```
   POST /api/batches/{id}/classify_batch/
   ```
   Corps de la requête (multipart/form-data) :
   ```
   images: [fichiers images multiples]
   use_tta: false (optionnel)
   ```

3. **Obtenir les classifications d'un lot** :
   ```
   GET /api/batches/{id}/classifications/
   ```

## Interface d'administration

L'interface d'administration est accessible à l'adresse `/admin/` et offre les fonctionnalités suivantes :

- Gestion des utilisateurs et des permissions
- Visualisation des fermes et de leurs statistiques
- Gestion des lots de prunes avec graphiques de distribution de qualité
- Visualisation des classifications individuelles
- Gestion des versions du modèle de classification
- Tableau de bord global avec statistiques

## Déploiement en production

### Avec Docker

1. Construire l'image :
   ```bash
   docker build -t plum-classification-api .
   ```

2. Exécuter le conteneur :
   ```bash
   docker run -p 8000:8000 -v /chemin/vers/models:/app/models plum-classification-api
   ```

### Sur un serveur

1. Installer les dépendances système :
   ```bash
   apt-get update && apt-get install -y python3 python3-pip libpq-dev
   ```

2. Configurer Gunicorn et Nginx :
   ```bash
   pip install gunicorn
   # Configurer Nginx comme proxy inverse
   ```

3. Configurer les variables d'environnement pour la production :
   ```bash
   export DEBUG=False
   export ALLOWED_HOSTS=votre-domaine.com
   # Autres variables d'environnement...
   ```

4. Collecter les fichiers statiques :
   ```bash
   python manage.py collectstatic
   ```

5. Démarrer le serveur avec Gunicorn :
   ```bash
   gunicorn plum_project.wsgi:application --bind 0.0.0.0:8000
   ```

## Développement

### Exécution des tests

```bash
python manage.py test
```

### Documentation de l'API

La documentation interactive de l'API est disponible aux adresses suivantes :

- Swagger UI : `/swagger/`
- ReDoc : `/redoc/`

## Dépannage

### Problèmes courants

1. **Erreur de chargement du modèle** :
   - Vérifier que le fichier .pt est présent dans le répertoire `models/`
   - Vérifier que le format du modèle est compatible avec PyTorch

2. **Erreur d'authentification** :
   - Vérifier que l'email a été vérifié
   - Vérifier que le token JWT n'a pas expiré

3. **Erreur de classification** :
   - Vérifier que l'image est au format JPEG/PNG
   - Vérifier que l'image est de bonne qualité et bien cadrée

### Journaux

Les journaux sont stockés dans le répertoire `logs/` et peuvent être consultés pour diagnostiquer les problèmes.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Contact

Pour toute question ou assistance, veuillez contacter support@plumclassifier.com.
