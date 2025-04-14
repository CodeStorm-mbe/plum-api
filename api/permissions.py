"""
Classes de permissions basées sur les rôles pour l'API.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission qui n'autorise que les administrateurs.
    """
    message = "Seuls les administrateurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsAgriculteur(permissions.BasePermission):
    """
    Permission qui n'autorise que les agriculteurs.
    """
    message = "Seuls les agriculteurs peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_agriculteur


class IsTechnicien(permissions.BasePermission):
    """
    Permission qui n'autorise que les techniciens.
    """
    message = "Seuls les techniciens peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_technicien


class IsConsultant(permissions.BasePermission):
    """
    Permission qui n'autorise que les consultants.
    """
    message = "Seuls les consultants peuvent effectuer cette action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_consultant


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission qui n'autorise que le propriétaire de l'objet ou un administrateur.
    """
    message = "Vous devez être le propriétaire de cet objet ou un administrateur."
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toujours accès
        if request.user.is_admin:
            return True
        
        # Vérifier si l'objet a un attribut user ou user_id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        
        # Pour les objets liés à une image de prune
        if hasattr(obj, 'plum_image') and hasattr(obj.plum_image, 'user'):
            return obj.plum_image.user == request.user
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission qui n'autorise que les méthodes de lecture.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission qui n'autorise que les utilisateurs avec email vérifié.
    """
    message = "Votre email doit être vérifié pour effectuer cette action."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email_verified


class RoleBasedPermission(permissions.BasePermission):
    """
    Permission basée sur les rôles avec des autorisations spécifiques par rôle.
    """
    def __init__(self, allowed_roles=None, read_roles=None):
        self.allowed_roles = allowed_roles or []
        self.read_roles = read_roles or []
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Vérifier si l'utilisateur a un rôle autorisé pour toutes les méthodes
        if request.user.role in self.allowed_roles:
            return True
        
        # Vérifier si l'utilisateur a un rôle autorisé pour les méthodes de lecture
        if request.method in permissions.SAFE_METHODS and request.user.role in self.read_roles:
            return True
        
        return False
