# Projet API Django pour la classification de prunes

## Tâches à réaliser

### Analyse et préparation
- [x] Examiner la documentation technique du modèle de classification de prunes
- [x] Analyser les fichiers Python fournis pour comprendre le modèle d'IA
- [x] Installer Django et les dépendances nécessaires
- [x] Installer PyTorch (version CPU) et les bibliothèques pour le modèle d'IA
- [x] Créer la structure du projet Django avec une approche modulaire

### Structure du projet
- [x] Créer le projet Django principal
- [x] Créer l'application API pour les endpoints
- [x] Créer l'application Users pour la gestion des utilisateurs et des rôles
- [x] Créer l'application Plum Classifier pour l'intégration du modèle d'IA
- [x] Configurer les paramètres du projet
- [x] Configurer les URLs du projet
- [x] Mettre en place la structure des dossiers pour les fichiers statiques et media

### Modèle de données
- [x] Implémenter les modèles de données avec UUIDs comme identifiants
- [x] Créer le modèle User personnalisé avec gestion des rôles
- [x] Créer le modèle pour stocker les résultats de classification
- [x] Créer le modèle pour les images de prunes
- [x] Créer les modèles pour la gestion des API et des notifications
- [x] Configurer les migrations

### Authentification et Communication
- [x] Implémenter l'authentification JWT pour l'application React
- [x] Configurer les endpoints d'authentification (login, refresh, register)
- [x] Implémenter la vérification d'email
- [x] Configurer les WebSockets pour les mises à jour en temps réel
- [x] Créer les consommateurs pour différents types de notifications

### Intégration du modèle d'IA
- [x] Créer un dossier pour stocker le modèle d'IA (.pt)
- [x] Implémenter le chargement du modèle d'IA
- [x] Créer le service de prétraitement des images
- [x] Implémenter les fonctions de prédiction
- [x] Intégrer avec les WebSockets pour les notifications en temps réel

### Développement des API Endpoints
- [x] Créer les sérialiseurs pour les modèles
- [x] Implémenter les vues pour la classification d'images
- [x] Développer les endpoints pour la gestion des utilisateurs
- [x] Créer les endpoints pour les opérations par lot
- [x] Documenter l'API avec drf-spectacular

### Gestion des rôles et système d'emails
- [x] Implémenter les permissions basées sur les rôles
- [x] Configurer le système d'envoi d'emails
- [x] Créer les templates d'emails
- [x] Implémenter les notifications par email
- [x] Tester le système d'emails avec différents types de notifications
- [x] Créer les rôles pour les agriculteurs et administrateurs
- [x] Implémenter les vues pour la gestion des rôles

### Tests et déploiement
- [ ] Écrire des tests unitaires pour les modèles
- [ ] Écrire des tests pour les endpoints API
- [ ] Écrire des tests pour l'intégration du modèle d'IA
- [ ] Configurer les paramètres de déploiement
- [ ] Préparer la documentation d'utilisation
