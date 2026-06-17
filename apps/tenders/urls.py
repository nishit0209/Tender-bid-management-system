from django.urls import path
from . import views

app_name = 'tenders'

urlpatterns = [
    path('', views.tender_list, name='list'),
    path('create/', views.tender_create, name='create'),
    path('<int:pk>/', views.tender_detail, name='detail'),
    path('<int:pk>/edit/', views.tender_edit, name='edit'),
    path('<int:pk>/submit/', views.tender_submit, name='submit'),
    path('<int:pk>/approve/', views.tender_approve, name='approve'),
    path('<int:pk>/reject/', views.tender_reject, name='reject'),
    path('<int:pk>/close/', views.tender_close, name='close'),
    path('<int:pk>/cancel/', views.tender_cancel, name='cancel'),
]
