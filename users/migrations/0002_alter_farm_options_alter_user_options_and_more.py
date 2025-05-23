# Generated by Django 5.1.3 on 2025-04-13 19:31

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="farm",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "ferme",
                "verbose_name_plural": "fermes",
            },
        ),
        migrations.AlterModelOptions(
            name="user",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "utilisateur",
                "verbose_name_plural": "utilisateurs",
            },
        ),
        migrations.AlterModelOptions(
            name="usersettings",
            options={
                "verbose_name": "paramètres utilisateur",
                "verbose_name_plural": "paramètres utilisateurs",
            },
        ),
        migrations.AlterModelManagers(
            name="user",
            managers=[],
        ),
        migrations.AddField(
            model_name="user",
            name="last_login_ip",
            field=models.GenericIPAddressField(
                blank=True, null=True, verbose_name="dernière IP de connexion"
            ),
        ),
        migrations.AlterField(
            model_name="farm",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="location",
            field=models.CharField(max_length=255, verbose_name="emplacement"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="name",
            field=models.CharField(max_length=100, verbose_name="nom"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="farms",
                to=settings.AUTH_USER_MODEL,
                verbose_name="propriétaire",
            ),
        ),
        migrations.AlterField(
            model_name="farm",
            name="size",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name="taille (hectares)",
            ),
        ),
        migrations.AlterField(
            model_name="farm",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
        ),
        migrations.AlterField(
            model_name="user",
            name="address",
            field=models.TextField(blank=True, null=True, verbose_name="adresse"),
        ),
        migrations.AlterField(
            model_name="user",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                max_length=254, unique=True, verbose_name="adresse email"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verification_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="date d'envoi de la vérification email",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verification_token",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=100,
                null=True,
                verbose_name="jeton de vérification email",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="email vérifié"),
        ),
        migrations.AlterField(
            model_name="user",
            name="organization",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="organisation"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="numéro de téléphone"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="profile_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="profile_images/",
                verbose_name="image de profil",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("farmer", "Agriculteur"),
                    ("technician", "Technicien"),
                    ("admin", "Administrateur"),
                ],
                default="farmer",
                max_length=20,
                verbose_name="rôle",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="language",
            field=models.CharField(
                choices=[("fr", "Français"), ("en", "Anglais"), ("es", "Espagnol")],
                default="fr",
                max_length=10,
                verbose_name="langue",
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="notification_preferences",
            field=models.JSONField(
                default=dict,
                help_text="Préférences pour les notifications par email, SMS, etc.",
                verbose_name="préférences de notification",
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="ui_preferences",
            field=models.JSONField(
                default=dict,
                help_text="Préférences pour l'interface utilisateur",
                verbose_name="préférences d'interface",
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="settings",
                to=settings.AUTH_USER_MODEL,
                verbose_name="utilisateur",
            ),
        ),
        migrations.AddIndex(
            model_name="farm",
            index=models.Index(fields=["owner"], name="users_farm_owner_i_aae706_idx"),
        ),
        migrations.AddIndex(
            model_name="farm",
            index=models.Index(fields=["name"], name="users_farm_name_3ed809_idx"),
        ),
        migrations.AddIndex(
            model_name="farm",
            index=models.Index(
                fields=["created_at"], name="users_farm_created_51c56f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="users_user_email_6f2530_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["role"], name="users_user_role_36d76d_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["email_verified"], name="users_user_email_v_d8053a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="usersettings",
            index=models.Index(fields=["user"], name="users_users_user_id_36e6ae_idx"),
        ),
    ]
