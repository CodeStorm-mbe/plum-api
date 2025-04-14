from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count

from .models import User, Farm, UserSettings

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'email_verified', 'is_active', 'created_at')
    list_filter = ('role', 'email_verified', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'password')
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Vérification d\'email', {
            'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')
        }),
        ('Informations supplémentaires', {
            'fields': ('phone_number', 'profile_image', 'organization', 'address')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    actions = ['verify_email', 'activate_users', 'deactivate_users']
    
    def verify_email(self, request, queryset):
        updated = queryset.update(email_verified=True)
        self.message_user(request, f"{updated} utilisateur(s) ont été vérifiés.")
    verify_email.short_description = "Marquer les emails comme vérifiés"
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateur(s) ont été activés.")
    activate_users.short_description = "Activer les utilisateurs sélectionnés"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateur(s) ont été désactivés.")
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'owner_link', 'size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def owner_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.username)
    owner_link.short_description = 'Propriétaire'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('owner')
        return queryset


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'language', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_link(self, obj):
        url = reverse("admin:users_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset
