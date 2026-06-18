"""
Root URL Configuration
Enterprise Tender & Bid Management System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ─────────────────────────────────────────────
# Admin Site Customization
# ─────────────────────────────────────────────
admin.site.site_header = 'Tender & Bid Management System'
admin.site.site_title = 'TenderBMS Admin'
admin.site.index_title = 'System Administration'

from django.http import HttpResponse

def fix_site(request):
    from django.contrib.sites.models import Site
    Site.objects.update_or_create(id=2, defaults={'domain': '127.0.0.1:8000', 'name': 'Localhost'})
    return HttpResponse("Site 2 successfully created! You can now use Google Login on Local.")

from apps.accounts.views_secure import secure_document_download

urlpatterns = [
    path('fix-site/', fix_site),
    # Django Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('auth/', include('allauth.urls')),

    # Secure File Download
    path('secure-download/<str:app_label>/<str:model_name>/<int:document_id>/<str:field_name>/', 
         secure_document_download, name='secure_download'),

    # Core Modules
    path('vendors/', include('apps.vendors.urls', namespace='vendors')),
    path('tenders/', include('apps.tenders.urls', namespace='tenders')),
    path('bids/', include('apps.bids.urls', namespace='bids')),
    path('evaluations/', include('apps.evaluations.urls', namespace='evaluations')),
    path('purchase-orders/', include('apps.purchase_orders.urls', namespace='purchase_orders')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('reports/', include('apps.reports.urls', namespace='reports')),

    # Dashboard (root redirect)
    path('', include('apps.accounts.urls_dashboard', namespace='dashboard')),
]

# Custom error handlers
handler404 = 'config.views.error_404'
handler500 = 'config.views.error_500'


# ─────────────────────────────────────────────
# Serve Media & Static in Development
# ─────────────────────────────────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
