from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class ChatterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatter"

    def ready(self):
        autodiscover_modules("chatter")
