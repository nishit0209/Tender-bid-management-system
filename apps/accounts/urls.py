from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',                          views.login_view,           name='login'),
    path('logout/',                         views.logout_view,          name='logout'),
    path('register/',                       views.register_view,        name='register'),
    path('profile/',                        views.profile_view,         name='profile'),
    path('change-password/',                views.change_password_view, name='change_password'),
    path('forgot-password/',                views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/',     views.reset_password_view,  name='reset_password'),

    # Admin: User Management
    path('system-logs/',                    views.system_logs_view,      name='system_logs'),
    path('users/',                          views.user_management_list,  name='user_management'),
    path('users/<int:pk>/edit/',            views.user_edit,             name='user_edit'),
    path('users/<int:pk>/toggle-active/',   views.user_toggle_active,    name='user_toggle_active'),
    path('users/<int:pk>/delete/',          views.user_delete,           name='user_delete'),
]
