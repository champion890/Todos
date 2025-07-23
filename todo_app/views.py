from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.conf import settings

from .models import Task
from .forms import TaskForm, UserRegistrationForm

import requests
import secrets

# Task Views
@method_decorator(login_required, name='dispatch')
class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    paginate_by = 4

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user).select_related('user').prefetch_related('tags')

        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')

        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if status == 'completed':
            queryset = queryset.filter(completed=True)
        elif status == 'pending':
            queryset = queryset.filter(completed=False)
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset


@method_decorator(login_required, name='dispatch')
class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')


@method_decorator(login_required, name='dispatch')
class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('task-list')
    else:
        form = UserRegistrationForm()
    return render(request, 'tasks/register.html', {'form': form})


# Discord OAuth2 Login Integration
def discord_login(request):
    state = secrets.token_urlsafe(16)
    request.session['discord_oauth_state'] = state

    auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={settings.DISCORD_SCOPE}"
        f"&state={state}"
    )
    return redirect(auth_url)


@csrf_exempt
def discord_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    if not code or state != request.session.get('discord_oauth_state'):
        return HttpResponseBadRequest("Invalid state or missing code.")

    # Step 1: Exchange code for access token
    token_response = requests.post(
        'https://discord.com/api/oauth2/token',
        data={
            'client_id': settings.DISCORD_CLIENT_ID,
            'client_secret': settings.DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.DISCORD_REDIRECT_URI,
            'scope': settings.DISCORD_SCOPE,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    token_data = token_response.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return HttpResponseBadRequest("Failed to obtain access token.")

    # Step 2: Get Discord user info
    user_response = requests.get(
        'https://discord.com/api/users/@me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    user_info = user_response.json()

    discord_email = user_info.get('email')
    discord_username = user_info.get('username')

    if not discord_email:
        return HttpResponseBadRequest("Discord account does not have public email.")

    # Step 3: Create or login the user
    user, created = User.objects.get_or_create(
        username=discord_email,
        defaults={'email': discord_email, 'first_name': discord_username}
    )

    auth_login(request, user)
    return redirect('task-list')
