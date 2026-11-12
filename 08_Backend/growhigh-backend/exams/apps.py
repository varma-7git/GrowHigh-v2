from django.apps import AppConfig


class ExamsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "exams"

    def ready(self):
        from . import signals  # noqa: F401  (re-marks results when a correct answer is changed)
