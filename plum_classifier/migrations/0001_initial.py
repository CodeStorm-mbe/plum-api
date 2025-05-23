# Generated by Django 5.2 on 2025-04-12 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ModelVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='nom')),
                ('version', models.CharField(max_length=20, verbose_name='version')),
                ('file_path', models.CharField(max_length=255, verbose_name='chemin du fichier')),
                ('metadata_path', models.CharField(blank=True, max_length=255, null=True, verbose_name='chemin des métadonnées')),
                ('model_type', models.CharField(max_length=50, verbose_name='type de modèle')),
                ('num_classes', models.PositiveIntegerField(verbose_name='nombre de classes')),
                ('input_shape', models.JSONField(default=list, verbose_name="forme d'entrée")),
                ('confidence_threshold', models.FloatField(default=0.7, verbose_name='seuil de confiance')),
                ('accuracy', models.FloatField(blank=True, null=True, verbose_name='précision')),
                ('f1_score', models.FloatField(blank=True, null=True, verbose_name='score F1')),
                ('precision', models.FloatField(blank=True, null=True, verbose_name='précision')),
                ('recall', models.FloatField(blank=True, null=True, verbose_name='rappel')),
                ('training_date', models.DateTimeField(blank=True, null=True, verbose_name="date d'entraînement")),
                ('training_duration', models.FloatField(blank=True, null=True, verbose_name="durée d'entraînement (h)")),
                ('dataset_size', models.PositiveIntegerField(blank=True, null=True, verbose_name='taille du jeu de données')),
                ('is_active', models.BooleanField(default=False, verbose_name='actif')),
                ('is_production', models.BooleanField(default=False, verbose_name='en production')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mis à jour le')),
            ],
            options={
                'verbose_name': 'version du modèle',
                'verbose_name_plural': 'versions du modèle',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='titre')),
                ('message', models.TextField(verbose_name='message')),
                ('type', models.CharField(choices=[('info', 'Information'), ('warning', 'Avertissement'), ('error', 'Erreur'), ('success', 'Succès')], default='info', max_length=10, verbose_name='type')),
                ('is_read', models.BooleanField(default=False, verbose_name='lu')),
                ('content_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='type de contenu')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name="ID de l'objet")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
            ],
            options={
                'verbose_name': 'notification',
                'verbose_name_plural': 'notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PlumBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='nom')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('classified', 'Classifié'), ('archived', 'Archivé')], default='pending', max_length=20, verbose_name='statut')),
                ('classification_summary', models.JSONField(blank=True, default=dict, verbose_name='résumé de classification')),
                ('total_plums', models.PositiveIntegerField(default=0, verbose_name='nombre total de prunes')),
                ('quality_distribution', models.JSONField(blank=True, default=dict, verbose_name='distribution de qualité')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='mis à jour le')),
            ],
            options={
                'verbose_name': 'lot de prunes',
                'verbose_name_plural': 'lots de prunes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PlumClassification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_path', models.CharField(max_length=255, verbose_name="chemin de l'image")),
                ('original_filename', models.CharField(blank=True, max_length=255, null=True, verbose_name='nom de fichier original')),
                ('classification_result', models.JSONField(default=dict, verbose_name='résultat de classification')),
                ('class_name', models.CharField(choices=[('bonne_qualite', 'Bonne qualité'), ('non_mure', 'Non mûre'), ('tachetee', 'Tachetée'), ('fissuree', 'Fissurée'), ('meurtrie', 'Meurtrie'), ('pourrie', 'Pourrie')], max_length=20, verbose_name='classe')),
                ('confidence_score', models.FloatField(verbose_name='score de confiance')),
                ('is_plum', models.BooleanField(default=True, verbose_name='est une prune')),
                ('processing_time', models.FloatField(blank=True, null=True, verbose_name='temps de traitement (s)')),
                ('device_info', models.TextField(blank=True, null=True, verbose_name="informations sur l'appareil")),
                ('geo_location', models.JSONField(blank=True, null=True, verbose_name='localisation géographique')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='créé le')),
            ],
            options={
                'verbose_name': 'classification de prune',
                'verbose_name_plural': 'classifications de prunes',
                'ordering': ['-created_at'],
            },
        ),
    ]
