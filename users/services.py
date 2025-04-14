"""
Configuration du système d'emails pour l'application.
"""

import os
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

# Configuration du logging
logger = logging.getLogger(__name__)

class EmailService:
    """
    Service pour l'envoi d'emails.
    """
    
    @staticmethod
    def send_email(to_email, subject, template_name, context, attachments=None):
        """
        Envoie un email en utilisant un template HTML et sa version texte.
        
        Args:
            to_email: Adresse email du destinataire ou liste d'adresses
            subject: Sujet de l'email
            template_name: Nom du template (sans extension)
            context: Dictionnaire de contexte pour le template
            attachments: Liste de tuples (nom_fichier, contenu, type_mime) ou None
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        try:
            # Ajouter des variables de contexte communes
            context['site_name'] = 'Système de Classification de Prunes'
            context['current_year'] = timezone.now().year
            
            # Rendre les templates HTML et texte
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Créer l'email
            if isinstance(to_email, list):
                email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, to_email)
            else:
                email = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
            
            # Ajouter la version HTML
            email.attach_alternative(html_content, "text/html")
            
            # Ajouter les pièces jointes
            if attachments:
                for attachment in attachments:
                    email.attach(*attachment)
            
            # Envoyer l'email
            email.send()
            logger.info(f"Email '{subject}' envoyé à {to_email}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email '{subject}' à {to_email}: {e}")
            return False
    
    @classmethod
    def send_verification_email(cls, user, verification_url):
        """
        Envoie un email de vérification.
        
        Args:
            user: Instance de l'utilisateur
            verification_url: URL de vérification
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        subject = "Vérification de votre adresse email"
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiration_hours': 24  # Les tokens expirent après 24 heures
        }
        return cls.send_email(user.email, subject, 'verification_email', context)
    
    @classmethod
    def send_password_reset_email(cls, user, reset_url):
        """
        Envoie un email de réinitialisation de mot de passe.
        
        Args:
            user: Instance de l'utilisateur
            reset_url: URL de réinitialisation
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        subject = "Réinitialisation de votre mot de passe"
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiration_hours': 24  # Les tokens expirent après 24 heures
        }
        return cls.send_email(user.email, subject, 'password_reset', context)
    
    @classmethod
    def send_classification_result_email(cls, user, classification_result, image_url=None):
        """
        Envoie un email avec les résultats de classification.
        
        Args:
            user: Instance de l'utilisateur
            classification_result: Instance du résultat de classification
            image_url: URL de l'image (optionnel)
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not user.notification_classification:
            logger.info(f"L'utilisateur {user.email} a désactivé les notifications de classification")
            return False
        
        subject = "Résultat de classification de prune"
        context = {
            'user': user,
            'result': classification_result,
            'image_url': image_url,
            'confidence_percent': int(classification_result.confidence * 100)
        }
        return cls.send_email(user.email, subject, 'classification_result', context)
    
    @classmethod
    def send_batch_completion_email(cls, user, batch_job, report_url=None):
        """
        Envoie un email de notification de fin de traitement par lot.
        
        Args:
            user: Instance de l'utilisateur
            batch_job: Instance de la tâche par lot
            report_url: URL du rapport (optionnel)
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not user.notification_reports:
            logger.info(f"L'utilisateur {user.email} a désactivé les notifications de rapports")
            return False
        
        subject = "Traitement par lot terminé"
        context = {
            'user': user,
            'batch_job': batch_job,
            'report_url': report_url,
            'success_rate': int((batch_job.success_count / batch_job.total_images) * 100) if batch_job.total_images > 0 else 0
        }
        return cls.send_email(user.email, subject, 'batch_completion', context)
    
    @classmethod
    def send_welcome_email(cls, user):
        """
        Envoie un email de bienvenue.
        
        Args:
            user: Instance de l'utilisateur
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        subject = "Bienvenue sur notre plateforme de classification de prunes"
        context = {
            'user': user,
        }
        return cls.send_email(user.email, subject, 'welcome', context)
    
    @classmethod
    def send_notification_email(cls, user, notification):
        """
        Envoie un email pour une notification.
        
        Args:
            user: Instance de l'utilisateur
            notification: Instance de la notification
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not user.notification_email:
            logger.info(f"L'utilisateur {user.email} a désactivé les notifications par email")
            return False
        
        subject = notification.title
        context = {
            'user': user,
            'notification': notification,
        }
        
        # Marquer la notification comme envoyée par email
        notification.is_sent_by_email = True
        notification.save(update_fields=['is_sent_by_email'])
        
        return cls.send_email(user.email, subject, 'notification', context)
