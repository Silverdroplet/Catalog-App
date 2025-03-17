from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.signals
        """Ensure groups exist when the app starts."""
        from django.contrib.auth.models import Group
        try:
            Group.objects.get_or_create(name="Librarians")
        except (OperationalError, ProgrammingError):
            pass
        try: 
            Group.objects.get_or_create(name="Patrons")
        except (OperationalError, ProgrammingError):
            pass
