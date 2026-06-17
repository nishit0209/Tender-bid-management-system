from django.urls import path
from . import views

app_name = 'bids'

urlpatterns = [
    path('', views.bid_list, name='list'),
    path('<int:pk>/', views.bid_detail, name='detail'),
    path('create/<int:tender_pk>/', views.bid_create, name='create'),
    path('<int:pk>/withdraw/', views.bid_withdraw, name='withdraw'),
]
