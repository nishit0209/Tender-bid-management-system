from django.apps import AppConfig


class PurchaseOrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchase_orders'
    verbose_name = 'Purchase Orders'

    def ready(self):
        import apps.purchase_orders.signals  # noqa: F401
