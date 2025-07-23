from django.urls import path
from .views import (
    TaskListView, TaskCreateView, TaskUpdateView, TaskDeleteView,
    register, discord_login, discord_callback  # 👈 Add these imports
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Task Views
    path('', TaskListView.as_view(), name='task-list'),
    path('add/', TaskCreateView.as_view(), name='task-add'),
    path('edit/<int:pk>/', TaskUpdateView.as_view(), name='task-edit'),
    path('delete/<int:pk>/', TaskDeleteView.as_view(), name='task-delete'),

    # Auth Views
    path('login/', auth_views.LoginView.as_view(template_name='tasks/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),

    #  Discord OAuth2
    path('discord/login/', discord_login, name='discord_login'),
    path('discord/callback/', discord_callback, name='discord_callback'),
]
