FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/media /app/static /app/staticfiles /app/logs /app/models

ENV DJANGO_SETTINGS_MODULE=plum_project.settings
RUN python manage.py collectstatic --noinput

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBUG=False

EXPOSE 8000

CMD ["gunicorn", "--workers=1", "--bind", "0.0.0.0:8000", "plum_project.wsgi:application"]
