from django.apps import AppConfig # type: ignore


class AppConfig(AppConfig):   # type: ignore
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        import app.signals 