from django.urls import path
from apps.accounts import views as acc_views

app_name = 'dashboard'

urlpatterns = [
    path('',                         acc_views.index,                name='index'),
    path('dashboard/admin/',         acc_views.admin_dashboard,      name='admin'),
    path('dashboard/procurement/',   acc_views.procurement_dashboard, name='procurement'),
    path('dashboard/manager/',       acc_views.manager_dashboard,    name='manager'),
    path('dashboard/vendor/',        acc_views.vendor_dashboard,     name='vendor'),
]
