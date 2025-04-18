"""
Module pour la validation des entrées utilisateur et la sécurisation des fichiers.
Fournit des fonctions pour valider et sécuriser les données entrantes.
"""

import os
import magic
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class FileSecurity:
    """
    Classe pour la validation et la sécurisation des fichiers uploadés.
    """
    
    # Types MIME autorisés pour les images
    ALLOWED_IMAGE_MIMETYPES = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif'
    ]
    
    # Extensions autorisées pour les images
    ALLOWED_IMAGE_EXTENSIONS = settings.ALLOWED_IMAGE_FORMATS
    
    # Taille maximale de fichier (en octets)
    MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE
    
    @staticmethod
    def validate_file_type(file, allowed_mimetypes=None):
        """
        Valide le type MIME d'un fichier.
        
        Args:
            file: Le fichier à valider
            allowed_mimetypes: Liste des types MIME autorisés (utilise les images par défaut)
            
        Returns:
            bool: True si le fichier est valide
            
        Raises:
            ValidationError: Si le fichier n'est pas valide
        """
        if allowed_mimetypes is None:
            allowed_mimetypes = FileSecurity.ALLOWED_IMAGE_MIMETYPES
            
        # Vérifier si le fichier est vide
        if not file or file.size == 0:
            raise ValidationError(_("Le fichier est vide."))
            
        # Lire les premiers octets du fichier pour déterminer son type
        file_mime = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # Réinitialiser le pointeur de fichier
        
        if file_mime not in allowed_mimetypes:
            raise ValidationError(
                _("Type de fichier non autorisé. Types autorisés: %(types)s"),
                params={'types': ', '.join(allowed_mimetypes)}
            )
            
        return True
    
    @staticmethod
    def validate_file_extension(file, allowed_extensions=None):
        """
        Valide l'extension d'un fichier.
        
        Args:
            file: Le fichier à valider
            allowed_extensions: Liste des extensions autorisées (utilise les images par défaut)
            
        Returns:
            bool: True si le fichier est valide
            
        Raises:
            ValidationError: Si le fichier n'est pas valide
        """
        if allowed_extensions is None:
            allowed_extensions = FileSecurity.ALLOWED_IMAGE_EXTENSIONS
            
        validator = FileExtensionValidator(allowed_extensions=allowed_extensions)
        try:
            validator(file)
            return True
        except ValidationError as e:
            raise ValidationError(
                _("Extension de fichier non autorisée. Extensions autorisées: %(exts)s"),
                params={'exts': ', '.join(allowed_extensions)}
            )
    
    @staticmethod
    def validate_file_size(file, max_size=None):
        """
        Valide la taille d'un fichier.
        
        Args:
            file: Le fichier à valider
            max_size: Taille maximale en octets (utilise la valeur des paramètres par défaut)
            
        Returns:
            bool: True si le fichier est valide
            
        Raises:
            ValidationError: Si le fichier est trop grand
        """
        if max_size is None:
            max_size = FileSecurity.MAX_FILE_SIZE
            
        if file.size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise ValidationError(
                _("Le fichier est trop volumineux. Taille maximale: %(size)s MB"),
                params={'size': max_size_mb}
            )
            
        return True
    
    @staticmethod
    def validate_image(file):
        """
        Valide un fichier image (type, extension et taille).
        
        Args:
            file: Le fichier image à valider
            
        Returns:
            bool: True si l'image est valide
            
        Raises:
            ValidationError: Si l'image n'est pas valide
        """
        FileSecurity.validate_file_type(file, FileSecurity.ALLOWED_IMAGE_MIMETYPES)
        FileSecurity.validate_file_extension(file, FileSecurity.ALLOWED_IMAGE_EXTENSIONS)
        FileSecurity.validate_file_size(file, FileSecurity.MAX_FILE_SIZE)
        return True
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Nettoie un nom de fichier pour éviter les problèmes de sécurité.
        
        Args:
            filename: Le nom de fichier à nettoyer
            
        Returns:
            str: Le nom de fichier nettoyé
        """
        # Extraire l'extension
        base, ext = os.path.splitext(filename)
        
        # Supprimer les caractères spéciaux et les espaces
        import re
        base = re.sub(r'[^\w\-]', '_', base)
        
        # Limiter la longueur du nom de base
        if len(base) > 100:
            base = base[:100]
            
        # Reconstruire le nom de fichier
        return f"{base}{ext}"
    
    @staticmethod
    def get_safe_upload_path(file, upload_dir, prefix=''):
        """
        Génère un chemin d'upload sécurisé pour un fichier.
        
        Args:
            file: Le fichier à uploader
            upload_dir: Le répertoire d'upload
            prefix: Préfixe optionnel pour le nom de fichier
            
        Returns:
            str: Le chemin d'upload sécurisé
        """
        import uuid
        
        # Nettoyer le nom de fichier
        original_name = FileSecurity.sanitize_filename(file.name)
        
        # Extraire l'extension
        _, ext = os.path.splitext(original_name)
        
        # Générer un nom de fichier unique
        unique_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(upload_dir, exist_ok=True)
        
        # Retourner le chemin complet
        return os.path.join(upload_dir, unique_name)


class InputValidation:
    """
    Classe pour la validation des entrées utilisateur.
    """
    
    @staticmethod
    def validate_coordinates(latitude, longitude):
        """
        Valide des coordonnées géographiques.
        
        Args:
            latitude: La latitude à valider
            longitude: La longitude à valider
            
        Returns:
            bool: True si les coordonnées sont valides
            
        Raises:
            ValidationError: Si les coordonnées ne sont pas valides
        """
        try:
            lat = float(latitude)
            lng = float(longitude)
            
            if not (-90 <= lat <= 90):
                raise ValidationError(_("La latitude doit être comprise entre -90 et 90."))
                
            if not (-180 <= lng <= 180):
                raise ValidationError(_("La longitude doit être comprise entre -180 et 180."))
                
            return True
        except (ValueError, TypeError):
            raise ValidationError(_("Les coordonnées doivent être des nombres."))
    
    @staticmethod
    def sanitize_html(html_content):
        """
        Nettoie du contenu HTML pour éviter les attaques XSS.
        
        Args:
            html_content: Le contenu HTML à nettoyer
            
        Returns:
            str: Le contenu HTML nettoyé
        """
        import bleach
        
        # Définir les balises et attributs autorisés
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
            'li', 'ol', 'p', 'strong', 'ul', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        
        allowed_attrs = {
            'a': ['href', 'title'],
            'abbr': ['title'],
            'acronym': ['title'],
        }
        
        # Nettoyer le HTML
        return bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )
    
    @staticmethod
    def validate_phone_number(phone):
        """
        Valide un numéro de téléphone.
        
        Args:
            phone: Le numéro de téléphone à valider
            
        Returns:
            bool: True si le numéro est valide
            
        Raises:
            ValidationError: Si le numéro n'est pas valide
        """
        import re
        
        # Supprimer les espaces, tirets, parenthèses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Vérifier que le numéro contient uniquement des chiffres et éventuellement un + au début
        if not re.match(r'^\+?\d{8,15}$', phone):
            raise ValidationError(_("Le numéro de téléphone n'est pas valide."))
            
        return True
