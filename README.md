# Projet Plum API Amélioré

## Vue d'ensemble

Plum API est une application Django avec Django REST Framework qui fournit une API pour la classification automatique des prunes destinée aux agriculteurs. L'application utilise un modèle de machine learning pour classifier les images de prunes selon leur qualité.

Ce projet a été amélioré pour résoudre plusieurs problèmes d'architecture, de sécurité, de performance et de maintenabilité, tout en enrichissant les fonctionnalités du dashboard.

## Structure du projet

Le projet est organisé en plusieurs applications Django:

- **users**: Gestion des utilisateurs avec différents rôles (agriculteur, technicien, administrateur)
- **authentication**: Système d'authentification avec JWT
- **plum_classifier**: Cœur du système de classification des prunes avec modèle ML
- **dashboard**: Interface pour visualiser les données et les statistiques
- **api**: Configuration générale de l'API et utilitaires

## Principales améliorations

1. **Sécurisation des informations sensibles**
   - Utilisation de variables d'environnement pour les informations sensibles
   - Configuration CORS sécurisée
   - Validation approfondie des entrées utilisateur et des fichiers

2. **Amélioration de l'architecture**
   - Séparation des environnements (développement, production)
   - Configuration conditionnelle des services
   - Paramètres de configuration centralisés

3. **Optimisation des performances**
   - Module d'optimisations pour les requêtes de base de données
   - Configuration du cache
   - Traitement par lots pour les grands ensembles de données

4. **Renforcement de la maintenabilité**
   - Module d'utilitaires pour la gestion des réponses API et des exceptions
   - Documentation complète
   - Tests unitaires

5. **Enrichissement des fonctionnalités du dashboard**
   - Module d'analyse avancée avec séries temporelles, comparaisons et prédictions
   - Nouveaux endpoints API pour les analyses
   - Visualisations améliorées

6. **Amélioration de la documentation**
   - Documentation complète de l'architecture, de l'API et des bonnes pratiques
   - Guides de déploiement et d'utilisation
   - Docstrings détaillés

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-depot>
   cd plum_project
   ```

2. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Modifier les valeurs dans .env selon votre environnement
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   ```

5. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

6. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

## Documentation

Pour plus de détails sur les améliorations apportées, consultez les documents suivants:

- [Documentation des améliorations](AMELIORATIONS.md): Détails sur toutes les améliorations apportées au projet
- [Guide des tests](TEST_README.md): Instructions pour exécuter les tests
- [Documentation de l'API](api/documentation.py): Documentation complète de l'API

## Utilisation

### API d'authentification

```
POST /api/auth/token/
```

Paramètres:
- `username`: Nom d'utilisateur ou email
- `password`: Mot de passe

### Classification des prunes

```
POST /api/plum-classifier/classify/
```

Paramètres:
- `image`: Fichier image de la prune
- `farm_id`: ID de la ferme (optionnel)
- `batch_id`: ID du lot (optionnel)

### Dashboard

```
GET /api/dashboard/user/
```

Pour plus de détails sur les endpoints disponibles, consultez la documentation de l'API.

## Licence

Ce projet est sous licence [MIT](LICENSE).
