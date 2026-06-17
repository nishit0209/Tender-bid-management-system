from django.apps import AppConfig


class EvaluationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.evaluations'
    verbose_name = 'Bid Evaluation'

    def ready(self):
        import apps.evaluations.signals  # noqa: F401
