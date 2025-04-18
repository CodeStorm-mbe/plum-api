# Guide d'exécution des tests

Pour exécuter les tests du projet Plum API, suivez ces étapes :

## Prérequis

1. Installer les dépendances requises :
```bash
pip install django djangorestframework django-cors-headers drf-spectacular python-dotenv dj-database-url python-magic bleach
```

2. Configurer l'environnement :
```bash
cp .env.example .env
# Modifier les valeurs dans .env selon votre environnement
```

## Exécution des tests

```bash
cd /chemin/vers/plum_project
python manage.py test
```

## Notes sur les tests

Les tests sont organisés en plusieurs catégories :

1. **SecurityTests** : Vérifie les améliorations de sécurité
   - Test des variables d'environnement
   - Test des paramètres CORS
   - Test de la validation des fichiers
   - Test de la validation des entrées utilisateur

2. **PerformanceTests** : Vérifie les optimisations de performance
   - Test du décorateur query_debugger
   - Test de la fonction optimize_queryset

3. **DashboardTests** : Vérifie les fonctionnalités du dashboard
   - Test des préférences utilisateur
   - Test de l'API du dashboard

4. **UtilsTests** : Vérifie les utilitaires
   - Test de ResponseBuilder
   - Test de ServiceBase

## Résultats attendus

Tous les tests devraient passer avec succès, démontrant que les améliorations implémentées fonctionnent correctement.

## Dépannage

Si vous rencontrez des erreurs :

1. Vérifiez que toutes les dépendances sont installées
2. Assurez-vous que le fichier .env est correctement configuré
3. Vérifiez que la base de données est accessible
4. Consultez les logs pour plus de détails sur les erreurs
