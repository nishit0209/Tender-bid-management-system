from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('',                          views.vendor_list,       name='list'),
    path('create/',                    views.vendor_create,     name='create'),
    path('my-profile/',                views.vendor_my_profile, name='my_profile'),
    path('<int:pk>/',                  views.vendor_detail,     name='detail'),
    path('<int:pk>/edit/',             views.vendor_update,     name='update'),
    path('<int:pk>/verify/',           views.vendor_verify,     name='verify'),
    path('<int:pk>/approve/',          views.vendor_approve,    name='approve'),
    path('<int:pk>/reject/',           views.vendor_reject,     name='reject'),
    path('<int:pk>/suspend/',          views.vendor_suspend,    name='suspend'),
    path('<int:pk>/reset-limits/',     views.vendor_reset_limits, name='reset_limits'),
    path('<int:vendor_pk>/upload-document/',  views.document_upload,   name='document_upload'),
    path('document/<int:doc_pk>/verify/',  views.document_verify,  name='document_verify'),
    path('document/<int:doc_pk>/delete/',  views.document_delete,  name='document_delete'),
    path('<int:pk>/delete/',           views.vendor_delete,     name='delete'),
]
