from django.urls import path
from .views import TaskListView, TaskCreateView, TaskUpdateView, TaskDeleteView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('add/', TaskCreateView.as_view(), name='task-add'),
    path('edit/<int:pk>/', TaskUpdateView.as_view(), name='task-edit'),
    path('delete/<int:pk>/', TaskDeleteView.as_view(), name='task-delete'),

    path('login/', auth_views.LoginView.as_view(template_name='tasks/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
