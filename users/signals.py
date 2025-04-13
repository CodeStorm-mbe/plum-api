from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import User, UserSettings


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil de paramètres pour les nouveaux utilisateurs.
    """
    if created:
        UserSettings.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    """
    Envoie un email de vérification aux nouveaux utilisateurs.
    """
    # Vérifier si c'est un nouvel utilisateur et qu'il n'est pas déjà vérifié
    if created and not instance.email_verified and instance.email:
        # Générer un token de vérification s'il n'en a pas déjà un
        if not instance.email_verification_token:
            instance.generate_email_verification_token()
        
        # Construire l'URL de vérification
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{instance.email_verification_token}"
        
        # Préparer le contexte pour le template d'email
        context = {
            'user': instance,
            'verification_url': verification_url,
            'site_name': 'Système de Classification des Prunes',
            'expiration_hours': 48
        }
        
        # Rendre le template HTML et le convertir en texte brut
        html_message = render_to_string('authentication/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        # Envoyer l'email
        try:
            send_mail(
                subject='Vérifiez votre adresse email',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Mettre à jour la date d'envoi
            instance.email_verification_sent_at = timezone.now()
            instance.save(update_fields=['email_verification_sent_at'])
        except Exception as e:
            # Loguer l'erreur mais ne pas la propager
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi de l'email de vérification à {instance.email}: {str(e)}")


@receiver(pre_save, sender=User)
def check_email_change(sender, instance, **kwargs):
    """
    Réinitialise la vérification d'email si l'adresse email est modifiée.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.email != instance.email:
                # L'email a été modifié, réinitialiser la vérification
                instance.email_verified = False
                instance.email_verification_token = None
                instance.email_verification_sent_at = None
        except User.DoesNotExist:
            pass  # Nouvel utilisateur, pas besoin de vérifier les changements
