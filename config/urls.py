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
    Site.objects.update_or_create(id=1, defaults={'domain': '127.0.0.1:8000', 'name': 'Localhost'})
    Site.objects.update_or_create(id=2, defaults={'domain': 'tenderbms.vercel.app', 'name': 'Production'})
    return HttpResponse("Site 1 & 2 successfully configured! You can now use Google Login on Local.")

def run_migrations(request):
    from django.core.management import call_command
    import io
    out = io.StringIO()
    try:
        call_command('makemigrations', stdout=out)
        call_command('migrate', 'socialaccount', '--fake', stdout=out)
        call_command('migrate', '--fake-initial', stdout=out)
        return HttpResponse(f"<pre>Migrations Successful!\n\n{out.getvalue()}</pre>")
    except Exception as e:
        return HttpResponse(f"<pre>Error running migrations:\n\n{str(e)}\n\nOutput so far:\n{out.getvalue()}</pre>")

def list_models(request):
    import urllib.request, json
    from decouple import config
    api_key = config('GEMINI_API_KEY', default='').strip()
    req = urllib.request.Request(f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}')
    res = urllib.request.urlopen(req)
    return HttpResponse(f"<pre>{json.dumps(json.loads(res.read()), indent=2)}</pre>")

from apps.accounts.views_secure import secure_document_download

urlpatterns = [
    path('fix-site/', fix_site),
    path('run-migrations/', run_migrations),
    path('list-models/', list_models),
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
