"""
Module de documentation pour le projet Plum API.
Contient des informations sur l'architecture, les bonnes pratiques et les guides d'utilisation.
"""

class ProjectDocumentation:
    """
    Documentation du projet Plum API.
    """
    
    @staticmethod
    def get_architecture_overview():
        """
        Aperçu de l'architecture du projet.
        
        Returns:
            str: Description de l'architecture
        """
        return """
# Architecture du projet Plum API

## Vue d'ensemble

Le projet Plum API est une application Django avec Django REST Framework qui fournit une API pour la classification automatique des prunes destinée aux agriculteurs. L'application utilise un modèle de machine learning pour classifier les images de prunes selon leur qualité.

## Structure du projet

Le projet est organisé en plusieurs applications Django:

- **users**: Gestion des utilisateurs avec différents rôles (agriculteur, technicien, administrateur)
- **authentication**: Système d'authentification avec JWT
- **plum_classifier**: Cœur du système de classification des prunes avec modèle ML
- **dashboard**: Interface pour visualiser les données et les statistiques
- **api**: Configuration générale de l'API et utilitaires

## Flux de données

1. L'utilisateur s'authentifie via l'API d'authentification
2. L'utilisateur télécharge une image de prune
3. Le service de classification traite l'image et retourne les résultats
4. Les résultats sont stockés dans la base de données
5. Le dashboard affiche les statistiques et les tendances

## Modèles de données principaux

- **User**: Utilisateur du système avec différents rôles
- **Farm**: Ferme appartenant à un utilisateur
- **PlumBatch**: Lot de prunes à classifier
- **PlumClassification**: Classification individuelle d'une prune
- **ModelVersion**: Version du modèle de classification

## Composants techniques

- **Django REST Framework**: Pour l'API RESTful
- **JWT**: Pour l'authentification
- **PyTorch**: Pour le modèle de classification
- **Redis**: Pour le cache (optionnel)
- **Celery**: Pour les tâches asynchrones (optionnel)
"""
    
    @staticmethod
    def get_api_documentation():
        """
        Documentation de l'API.
        
        Returns:
            str: Documentation de l'API
        """
        return """
# Documentation de l'API Plum

## Authentification

### Obtenir un token

```
POST /api/auth/token/
```

Paramètres:
- `username`: Nom d'utilisateur ou email
- `password`: Mot de passe

Réponse:
```json
{
  "access": "token_jwt_access",
  "refresh": "token_jwt_refresh"
}
```

### Rafraîchir un token

```
POST /api/auth/token/refresh/
```

Paramètres:
- `refresh`: Token de rafraîchissement

Réponse:
```json
{
  "access": "nouveau_token_jwt_access"
}
```

## Classification des prunes

### Classifier une image

```
POST /api/plum-classifier/classify/
```

Paramètres:
- `image`: Fichier image de la prune
- `farm_id`: ID de la ferme (optionnel)
- `batch_id`: ID du lot (optionnel)
- `use_tta`: Utiliser Test Time Augmentation (optionnel, défaut: false)

Réponse:
```json
{
  "id": 123,
  "class_name": "bonne_qualite",
  "class_name_display": "Bonne qualité",
  "confidence_score": 0.95,
  "is_plum": true,
  "processing_time": 0.45,
  "created_at": "2025-04-18T12:34:56Z"
}
```

### Classifier un lot d'images

```
POST /api/plum-classifier/batches/{batch_id}/classify_batch/
```

Paramètres:
- `images`: Liste de fichiers images
- `use_tta`: Utiliser Test Time Augmentation (optionnel, défaut: false)

Réponse:
```json
{
  "batch_id": 45,
  "total_processed": 10,
  "total_images": 10,
  "status": "classified",
  "summary": {
    "total_plums": 10,
    "quality_distribution": {
      "bonne_qualite": {"count": 7, "percentage": 70.0},
      "tachetee": {"count": 2, "percentage": 20.0},
      "meurtrie": {"count": 1, "percentage": 10.0}
    },
    "average_confidence": 0.92
  }
}
```

## Dashboard

### Obtenir les données du dashboard

```
GET /api/dashboard/user/
```

Réponse:
```json
{
  "total_classifications": 150,
  "average_confidence": 0.89,
  "class_distribution": {
    "Bonne qualité": 105,
    "Tachetée": 25,
    "Meurtrie": 15,
    "Fissurée": 5
  },
  "class_percentages": {
    "Bonne qualité": 70.0,
    "Tachetée": 16.67,
    "Meurtrie": 10.0,
    "Fissurée": 3.33
  },
  "farms": [
    {
      "id": 1,
      "name": "Ferme des Pruniers",
      "location": "Agen, France",
      "total_classifications": 150,
      "total_batches": 15,
      "pending_batches": 2
    }
  ]
}
```

### Obtenir les tendances de qualité

```
GET /api/dashboard/analytics/quality_trends/?farm_id=1&period=week
```

Réponse:
```json
{
  "bonne_qualite": [
    {"date": "2025-04-01T00:00:00Z", "value": 25},
    {"date": "2025-04-08T00:00:00Z", "value": 30},
    {"date": "2025-04-15T00:00:00Z", "value": 35}
  ],
  "tachetee": [
    {"date": "2025-04-01T00:00:00Z", "value": 10},
    {"date": "2025-04-08T00:00:00Z", "value": 8},
    {"date": "2025-04-15T00:00:00Z", "value": 7}
  ]
}
```

### Obtenir une prédiction de qualité

```
GET /api/dashboard/analytics/quality_prediction/?farm_id=1&days_ahead=7
```

Réponse:
```json
{
  "prediction_date": "2025-04-25T12:34:56Z",
  "predicted_distribution": {
    "bonne_qualite": 72.5,
    "tachetee": 15.3,
    "meurtrie": 8.2,
    "fissuree": 4.0
  },
  "confidence": 0.85,
  "method": "moving_average"
}
```
"""
    
    @staticmethod
    def get_best_practices():
        """
        Bonnes pratiques pour le développement.
        
        Returns:
            str: Description des bonnes pratiques
        """
        return """
# Bonnes pratiques pour le développement

## Sécurité

1. **Ne jamais stocker d'informations sensibles dans le code**
   - Utiliser des variables d'environnement ou des fichiers .env
   - Ne pas committer de secrets dans le dépôt Git

2. **Valider toutes les entrées utilisateur**
   - Utiliser les classes de validation fournies dans `api.security`
   - Vérifier les types, tailles et formats des données

3. **Limiter les permissions**
   - Appliquer le principe du moindre privilège
   - Utiliser les classes de permission de DRF

## Performance

1. **Optimiser les requêtes de base de données**
   - Utiliser `select_related` et `prefetch_related` pour éviter les requêtes N+1
   - Utiliser les fonctions d'optimisation dans `api.optimizations`

2. **Utiliser le cache**
   - Mettre en cache les résultats coûteux à calculer
   - Utiliser le décorateur `@cached_queryset` pour les requêtes fréquentes

3. **Traiter les grands ensembles de données par lots**
   - Utiliser la fonction `batch_process` pour les opérations sur de grands ensembles

## Maintenabilité

1. **Suivre les conventions de nommage**
   - Utiliser des noms descriptifs pour les variables, fonctions et classes
   - Suivre les conventions PEP 8 pour le code Python

2. **Documenter le code**
   - Ajouter des docstrings à toutes les fonctions et classes
   - Expliquer le "pourquoi" plutôt que le "comment"

3. **Séparer les responsabilités**
   - Utiliser le pattern Service pour la logique métier
   - Garder les vues légères et déplacer la logique dans des services

4. **Écrire des tests**
   - Viser une couverture de code élevée
   - Tester les cas limites et les cas d'erreur

## Structure du code

1. **Organiser le code par fonctionnalité**
   - Créer des applications Django distinctes pour chaque domaine
   - Utiliser des modules pour regrouper les fonctionnalités connexes

2. **Utiliser des interfaces cohérentes**
   - Standardiser les réponses API avec `ResponseBuilder`
   - Utiliser des sérialiseurs pour la validation et la transformation des données

3. **Éviter la duplication de code**
   - Extraire les fonctionnalités communes dans des utilitaires
   - Utiliser l'héritage et la composition pour réutiliser le code
"""
    
    @staticmethod
    def get_deployment_guide():
        """
        Guide de déploiement.
        
        Returns:
            str: Guide de déploiement
        """
        return """
# Guide de déploiement

## Prérequis

- Python 3.10+
- PostgreSQL 14+
- Redis (optionnel, pour le cache et Celery)
- Serveur web (Nginx recommandé)

## Configuration de l'environnement

1. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate  # Windows
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement**
   - Copier `.env.example` vers `.env`
   - Modifier les valeurs selon l'environnement

## Base de données

1. **Créer la base de données PostgreSQL**
   ```bash
   createdb plum_db
   ```

2. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

3. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

## Déploiement

### Option 1: Déploiement avec Docker

1. **Construire l'image Docker**
   ```bash
   docker build -t plum-api .
   ```

2. **Exécuter le conteneur**
   ```bash
   docker run -p 8000:8000 --env-file .env plum-api
   ```

### Option 2: Déploiement sur un serveur

1. **Configurer Gunicorn**
   ```bash
   gunicorn plum_project.wsgi:application --bind 0.0.0.0:8000
   ```

2. **Configurer Nginx**
   ```nginx
   server {
       listen 80;
       server_name example.com;

       location /static/ {
           alias /path/to/staticfiles/;
       }

       location /media/ {
           alias /path/to/media/;
       }

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Configurer le service systemd**
   ```ini
   [Unit]
   Description=Plum API Gunicorn daemon
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/path/to/project
   ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 plum_project.wsgi:application
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

## Configuration du modèle ML

1. **Placer les fichiers du modèle**
   - Copier les fichiers du modèle dans le répertoire `models/`

2. **Enregistrer le modèle dans la base de données**
   ```bash
   python manage.py shell
   ```
   ```python
   from plum_classifier.models import ModelVersion
   ModelVersion.objects.create(
       name="EfficientNet B4",
       version="1.0.0",
       file_path="/path/to/models/efficientnet_b4.pt",
       metadata_path="/path/to/models/efficientnet_b4_metadata.json",
       model_type="efficientnet",
       num_classes=6,
       input_shape=[1, 3, 320, 320],
       confidence_threshold=0.7,
       is_active=True
   )
   ```

## Surveillance et maintenance

1. **Configurer la journalisation**
   - Les logs sont stockés dans le répertoire `logs/`
   - Configurer une rotation des logs avec logrotate

2. **Sauvegardes**
   - Configurer des sauvegardes régulières de la base de données
   - Sauvegarder également les fichiers média et les modèles

3. **Mises à jour**
   - Mettre à jour régulièrement les dépendances
   - Suivre les bonnes pratiques pour les migrations de base de données
"""

    @staticmethod
    def get_user_guide():
        """
        Guide d'utilisation pour les utilisateurs finaux.
        
        Returns:
            str: Guide d'utilisation
        """
        return """
# Guide d'utilisation de Plum API

## Introduction

Plum API est une application qui permet de classifier automatiquement des prunes selon leur qualité. Elle est destinée aux agriculteurs, techniciens et administrateurs du système.

## Rôles utilisateur

### Agriculteur

En tant qu'agriculteur, vous pouvez:
- Gérer vos fermes
- Télécharger des images de prunes pour classification
- Créer et gérer des lots de prunes
- Consulter les statistiques de vos classifications
- Voir les tendances de qualité de vos prunes

### Technicien

En tant que technicien, vous pouvez:
- Voir les données de toutes les fermes
- Analyser les performances des fermes
- Comparer les tendances de qualité entre différentes fermes
- Aider à résoudre les problèmes techniques

### Administrateur

En tant qu'administrateur, vous pouvez:
- Gérer tous les utilisateurs
- Voir toutes les données du système
- Gérer les versions du modèle de classification
- Surveiller les performances du système

## Fonctionnalités principales

### Classification d'images

1. **Classification individuelle**
   - Téléchargez une image de prune
   - Le système analyse l'image et détermine sa qualité
   - Les résultats sont affichés immédiatement

2. **Classification par lot**
   - Créez un nouveau lot
   - Téléchargez plusieurs images à la fois
   - Le système traite toutes les images et fournit un résumé

### Dashboard

1. **Vue d'ensemble**
   - Nombre total de classifications
   - Distribution des classes de qualité
   - Confiance moyenne des classifications

2. **Statistiques par ferme**
   - Performance de chaque ferme
   - Distribution de qualité par ferme
   - Tendances au fil du temps

3. **Prédictions**
   - Prédictions de qualité future basées sur les tendances historiques
   - Comparaison avec les moyennes du secteur

### Gestion des fermes

1. **Ajouter une ferme**
   - Nom et emplacement
   - Taille et description
   - Coordonnées géographiques (optionnel)

2. **Gérer les lots**
   - Créer des lots pour organiser les classifications
   - Suivre l'état des lots (en attente, classifié, archivé)
   - Voir les résumés de classification par lot

## Conseils d'utilisation

1. **Pour de meilleurs résultats de classification**
   - Prenez des photos bien éclairées
   - Centrez la prune dans l'image
   - Évitez les arrière-plans complexes
   - Utilisez une résolution d'au moins 640x640 pixels

2. **Utilisation efficace du dashboard**
   - Personnalisez votre vue selon vos besoins
   - Utilisez les filtres pour affiner les données
   - Exportez les données pour une analyse plus approfondie

3. **Gestion des lots**
   - Créez des lots distincts pour différentes variétés ou parcelles
   - Utilisez des noms descriptifs pour faciliter l'identification
   - Archivez les lots terminés pour garder votre interface organisée
"""

def generate_documentation():
    """
    Génère la documentation complète du projet.
    
    Returns:
        dict: Documentation complète
    """
    docs = ProjectDocumentation()
    
    return {
        "architecture": docs.get_architecture_overview(),
        "api": docs.get_api_documentation(),
        "best_practices": docs.get_best_practices(),
        "deployment": docs.get_deployment_guide(),
        "user_guide": docs.get_user_guide()
    }
