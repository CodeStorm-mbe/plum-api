# Utiliser une image légère
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système (pour Pillow, PyTorch, etc.)
RUN apt-get update && apt-get install -y \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du projet
COPY . .

# Exposer le port 8000
EXPOSE 8000

# Commande pour lancer Gunicorn avec 1 worker
CMD ["gunicorn", "--workers=1", "--bind", "0.0.0.0:8000", "plum_project.wsgi:application"]