from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, \
    PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from actions.models import Action
from actions.utils import create_action
from .forms import LoginForm, UserRegistrationForm, ProfileEditForm, UserEditForm
from .models import Profile, Contact


# def user_login(request):
#     template_name = 'account/login.html'
#     if request.method == 'POST':
#         form = LoginForm(request.POST)
#         if form.is_valid():
#             cd = form.cleaned_data
#             user = authenticate(request, username=cd['username'], password=cd['password'])
#             if user is not None:
#                 if user.is_active:
#                     login(request, user)
#                     return HttpResponse('Authenticated successfully')
#                 else:
#                     form.add_error(None, 'Disabled account')
#             else:
#                 form.add_error(None, 'Invalid login')
#     else:
#         form = LoginForm()
#     context = {
#         'form': form
#     }
#     return render(request, template_name, context)


@login_required
def dashboard(request):
    template_name = 'account/dashboard.html'
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)
    if following_ids:
        actions = actions.filter(user_id__in=following_ids)
    actions = actions.select_related('user', 'user__profile')[:10].prefetch_related('target')[:10]
    context = {
        'section': 'dashboard',
        'actions': actions
    }
    return render(request, template_name, context)


class AccountLoginView(LoginView):
    pass

class AccountLogoutView(LogoutView):
    pass


class AccountPasswordChangeView(PasswordChangeView):
    pass


class AccountPasswordChangeDoneView(PasswordChangeDoneView):
    pass


class AccountPasswordResetView(PasswordResetView):
    pass


class AccountPasswordResetDoneView(PasswordResetDoneView):
    pass


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    pass


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    pass


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            create_action(new_user, 'has created an account')
            Profile.objects.create(user=new_user)
            return render(request, 'account/register_done.html', {'new_user': new_user})
    else:
        form = UserRegistrationForm()
    return render(request, 'account/register.html', {'form': form})


@login_required
def edit(request):
    template_name = 'account/edit.html'
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile,
                                       data=request.POST,
                                       files=request.FILES
                                       )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated!!!')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, template_name, context)


@login_required
def user_list(request):
    template_name = 'account/user/list.html'
    users = User.objects.filter(is_active=True)
    context = {
        'users': users
    }
    return render(request, template_name, context)


@login_required
def user_detail(request, username):
    template_name = 'account/user/detail.html'
    user = get_object_or_404(User, username=username, is_active=True)
    context = {
        'user': user
    }
    return render(request, template_name, context)


@login_required
@require_POST
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(pk=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=user).delete()
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})