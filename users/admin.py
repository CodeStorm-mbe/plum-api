from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Farm, UserSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuration de l'interface d'administration pour le modèle User personnalisé.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'email_verified', 'is_staff')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'organization')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login_ip')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {'fields': ('email', 'first_name', 'last_name', 'profile_image')}),
        (_('Rôle et organisation'), {'fields': ('role', 'organization', 'address', 'phone_number')}),
        (_('Vérification'), {'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {'fields': ('last_login', 'created_at', 'updated_at', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle Farm.
    """
    list_display = ('name', 'owner', 'location', 'size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location', 'owner__username', 'owner__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('name', 'owner', 'description')}),
        (_('Localisation'), {'fields': ('location', 'latitude', 'longitude')}),
        (_('Détails'), {'fields': ('size',)}),
        (_('Dates'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        """
        Limite les fermes affichées aux administrateurs et aux propriétaires.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff or request.user.is_admin_user:
            return qs
        return qs.filter(owner=request.user)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface d'administration pour le modèle UserSettings.
    """
    list_display = ('user', 'language', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Préférences'), {'fields': ('language', 'notification_preferences', 'ui_preferences')}),
        (_('Dates'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_queryset(self, request):
        """
        Limite les paramètres affichés aux administrateurs et aux propriétaires.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.is_staff or request.user.is_admin_user:
            return qs
        return qs.filter(user=request.user)
