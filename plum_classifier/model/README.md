# Instructions pour le modèle d'IA

Ce dossier est destiné à contenir le fichier du modèle d'IA pour la classification des prunes.

## Comment ajouter le modèle

1. Placez le fichier `.pt` du modèle de classification de prunes dans ce dossier
2. Assurez-vous que le nom du fichier correspond à celui configuré dans les paramètres Django (`plum_classifier.pt` par défaut)
3. Le modèle sera automatiquement chargé par le service ModelService lors de la première utilisation

## Structure du modèle

Le modèle attendu est un modèle PyTorch basé sur EfficientNet avec des mécanismes d'attention et des connexions résiduelles, capable de classifier les prunes en 6 catégories différentes :

1. Bonne qualité
2. Non mûre
3. Tachetée
4. Fissurée
5. Meurtrie
6. Pourrie

## Paramètres du modèle

- Taille d'image attendue : 320x320 pixels
- Seuil de confiance : 0.7 (configurable dans les paramètres Django)
- Format du modèle : PyTorch (.pt)

## Remarque importante

Si vous modifiez le modèle, assurez-vous de mettre à jour la version du modèle dans le service de classification pour suivre les performances et les métriques correctement.
