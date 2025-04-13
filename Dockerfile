FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/media /app/static /app/logs /app/models

# Collecter les fichiers statiques (pour Django)
RUN python manage.py collectstatic --noinput

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False \
    # ALLOWED_HOSTS doit inclure le domaine Render
    ALLOWED_HOSTS=localhost,127.0.0.1,*.onrender.com

# Exposer le port (Render attend généralement 10000, mais 8000 fonctionne si configuré)
EXPOSE 8000

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "plum_project.wsgi:application"]