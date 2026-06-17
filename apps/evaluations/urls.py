from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    # Global list of tenders needing evaluation
    path('', views.evaluation_list, name='list'),

    # Shows leaderboard for a tender (for both Procurement and Manager based on role)
    path('tender/<int:tender_id>/', views.tender_evaluation_list, name='tender_evaluations'),
    
    # Evaluate a single bid
    path('bid/<int:bid_id>/evaluate/', views.evaluate_bid, name='evaluate_bid'),
    
    # Submit evaluated bids to Manager
    path('tender/<int:tender_id>/submit/', views.submit_evaluations, name='submit_evaluations'),
    
    # Manager approves one bid
    path('<int:evaluation_id>/approve/', views.approve_award, name='approve_award'),
]
