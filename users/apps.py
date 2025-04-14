from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    """
    Configuration de l'application users avec des signaux pour la gestion des événements.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = _('Utilisateurs et Fermes')

    def ready(self):
        """
        Importe les signaux lorsque l'application est prête.
        Cette méthode est appelée lorsque le registre des applications est entièrement peuplé.
        """
        import users.signals  # noqa
