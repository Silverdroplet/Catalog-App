from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Ensure groups exist when the app starts."""
        from django.contrib.auth.models import Group
        Group.objects.get_or_create(name="Librarians")
        Group.objects.get_or_create(name="Patrons")