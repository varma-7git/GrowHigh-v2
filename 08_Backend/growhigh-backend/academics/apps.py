from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "academics"

    def ready(self):
        from . import tracking  # noqa: F401  (lesson questions, career goals and auto-completion)
