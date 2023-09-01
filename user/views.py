from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator

from metrics.models import UserMetrics
from .forms import CustomUserCreationForm, UserProfileForm, LoginForm, CustomPasswordChangeForm


def register(request):
    context = {}
    register_form = CustomUserCreationForm()

    if request.method == 'POST':
        register_form = CustomUserCreationForm(request.POST)
        if register_form.is_valid():
            user = register_form.save()
            UserMetrics.objects.create(user=user)
            perform_login(request, user)
            return redirect(reverse('profile'))

    context['register_form'] = register_form
    return render(request, 'register.html', context)


def login_view(request):
    context = {}
    login_form = LoginForm()

    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.user
            perform_login(request, user)
            return redirect(reverse('home'))

    context['login_form'] = login_form
    return render(request, 'login.html', context)


def perform_login(request, user):
    login(request, user)


@method_decorator(login_required, name='dispatch')
class MyPasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    form_class = CustomPasswordChangeForm

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Your password has been changed successfully.')
        return redirect('change_password')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})
