# Generated by Django 5.1.3 on 2025-04-14 06:35

import django.contrib.auth.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_farm_options_alter_user_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="farm",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "farm",
                "verbose_name_plural": "farms",
            },
        ),
        migrations.AlterModelOptions(
            name="user",
            options={"verbose_name": "user", "verbose_name_plural": "users"},
        ),
        migrations.AlterModelOptions(
            name="usersettings",
            options={
                "verbose_name": "user settings",
                "verbose_name_plural": "user settings",
            },
        ),
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveIndex(
            model_name="farm",
            name="users_farm_owner_i_aae706_idx",
        ),
        migrations.RemoveIndex(
            model_name="farm",
            name="users_farm_name_3ed809_idx",
        ),
        migrations.RemoveIndex(
            model_name="farm",
            name="users_farm_created_51c56f_idx",
        ),
        migrations.RemoveIndex(
            model_name="user",
            name="users_user_email_6f2530_idx",
        ),
        migrations.RemoveIndex(
            model_name="user",
            name="users_user_role_36d76d_idx",
        ),
        migrations.RemoveIndex(
            model_name="user",
            name="users_user_email_v_d8053a_idx",
        ),
        migrations.RemoveIndex(
            model_name="usersettings",
            name="users_users_user_id_36e6ae_idx",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_login_ip",
        ),
        migrations.AlterField(
            model_name="farm",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="location",
            field=models.CharField(max_length=255, verbose_name="location"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="name",
            field=models.CharField(max_length=100, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="farm",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="farms",
                to=settings.AUTH_USER_MODEL,
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
                verbose_name="size (hectares)",
            ),
        ),
        migrations.AlterField(
            model_name="farm",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="updated at"),
        ),
        migrations.AlterField(
            model_name="user",
            name="address",
            field=models.TextField(blank=True, null=True, verbose_name="address"),
        ),
        migrations.AlterField(
            model_name="user",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                max_length=254, unique=True, verbose_name="email address"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verification_sent_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="email verification sent at"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verification_token",
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name="email verification token",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email_verified",
            field=models.BooleanField(default=False, verbose_name="email verified"),
        ),
        migrations.AlterField(
            model_name="user",
            name="organization",
            field=models.CharField(
                blank=True, max_length=100, null=True, verbose_name="organization"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="phone_number",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="phone number"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="profile_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="profile_images/",
                verbose_name="profile image",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("farmer", "Farmer"),
                    ("technician", "Technician"),
                    ("admin", "Administrator"),
                ],
                default="farmer",
                max_length=20,
                verbose_name="role",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="updated at"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="created at"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="language",
            field=models.CharField(
                default="en", max_length=10, verbose_name="language"
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="notification_preferences",
            field=models.JSONField(
                default=dict, verbose_name="notification preferences"
            ),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="ui_preferences",
            field=models.JSONField(default=dict, verbose_name="UI preferences"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="updated at"),
        ),
        migrations.AlterField(
            model_name="usersettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="settings",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
