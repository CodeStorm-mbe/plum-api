#!/bin/bash

# Script d'installation pour le projet Plum API

echo "Installation du projet Plum API..."

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Python 3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "pip3 n'est pas installé. Veuillez l'installer avant de continuer."
    exit 1
fi

# Créer un environnement virtuel
echo "Création de l'environnement virtuel..."
python3 -m venv venv

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo "Installation des dépendances..."
pip install -r requirements.txt

# Copier le fichier .env.example vers .env si .env n'existe pas
if [ ! -f .env ]; then
    echo "Création du fichier .env à partir de .env.example..."
    cp .env.example .env
    echo "Veuillez modifier le fichier .env avec vos propres valeurs."
fi

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

echo "Installation terminée avec succès!"
echo "Pour lancer le serveur de développement, exécutez: python manage.py runserver"
echo "Pour créer un superutilisateur, exécutez: python manage.py createsuperuser"
