from django.urls import path
from . import views

app_name = 'purchase_orders'

urlpatterns = [
    # PO Tracking Dashboard
    path('', views.po_list, name='list'),
    
    # Generate PO from a winning bid
    path('generate/<int:bid_id>/', views.po_generate, name='generate'),
    
    # View PO Detail
    path('<int:pk>/', views.po_detail, name='detail'),
    
    # Handle PO State Transitions (approve, dispatch, deliver, complete)
    path('<int:pk>/action/<str:action>/', views.po_action, name='action'),
]
