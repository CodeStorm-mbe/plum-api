#!/bin/bash
# dev.sh

echo "Generating migrations..."
python manage.py makemigrations

echo "Applying migrations..."
python manage.py migrate
