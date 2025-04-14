from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour permettre aux propriétaires d'un objet ou aux administrateurs
    de le modifier ou de le supprimer.
    """
    message = _("Vous devez être le propriétaire de cet objet ou un administrateur.")

    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_staff or request.user.is_admin_user:
            return True
        
        # Vérifier si l'objet a un attribut 'owner' ou 'user'
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Pour les objets User, vérifier si l'utilisateur est lui-même
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Permission personnalisée pour restreindre l'accès aux seuls administrateurs.
    """
    message = _("Vous devez être un administrateur pour effectuer cette action.")

    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_staff or request.user.is_admin_user))


class IsAuthenticatedAndVerified(permissions.BasePermission):
    """
    Permission personnalisée pour restreindre l'accès aux utilisateurs authentifiés
    dont l'email a été vérifié.
    """
    message = _("Vous devez avoir vérifié votre adresse email pour effectuer cette action.")

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.email_verified
        )


class IsFarmOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour permettre aux propriétaires d'une ferme ou aux administrateurs
    d'accéder à ses ressources associées.
    """
    message = _("Vous devez être le propriétaire de cette ferme ou un administrateur.")

    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_staff or request.user.is_admin_user:
            return True
        
        # Pour les objets qui ont une relation avec Farm
        if hasattr(obj, 'farm'):
            return obj.farm.owner == request.user
        
        # Pour les objets Farm
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement les méthodes de lecture.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
