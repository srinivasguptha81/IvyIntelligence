from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .models import StudentProfile
from .forms import ProfileUpdateForm, UserUpdateForm


@login_required
def profile_setup(request):
    """First-time profile setup for new users."""
    profile = request.user.studentprofile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid() and user_form.is_valid():
            user_form.save()
            form.save()
            messages.success(request, "Profile set up successfully!")
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=profile)
        user_form = UserUpdateForm(instance=request.user)

    return render(request, 'profiles/setup.html', {'form': form, 'user_form': user_form})


@login_required
def profile_edit(request):
    """Edit existing profile."""
    profile = request.user.studentprofile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        user_form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid() and user_form.is_valid():
            user_form.save()
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile_view', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile)
        user_form = UserUpdateForm(instance=request.user)

    return render(request, 'profiles/edit.html', {'form': form, 'user_form': user_form})


def profile_view(request, username):
    """Public profile page for any student, with inline edit for own profile."""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(StudentProfile, user=user)
    is_own_profile = request.user.is_authenticated and request.user == user

    # Form handling for inline edit
    from .forms import ProfileUpdateForm, UserUpdateForm
    user_form = None
    form = None

    if is_own_profile:
        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            user_form = UserUpdateForm(request.POST, instance=user)
            if form.is_valid() and user_form.is_valid():
                user_form.save()
                form.save()
                from django.contrib import messages
                messages.success(request, "Profile updated successfully!")
                return redirect('profile_view', username=username)
        else:
            form = ProfileUpdateForm(instance=profile)
            user_form = UserUpdateForm(instance=user)

    from apps.incoscore.models import Achievement
    achievements = Achievement.objects.filter(student=profile, verified=True)
    from apps.community.models import Post
    posts = Post.objects.filter(author=user).order_by('-created_at')[:5]
    from apps.applications.models import Application
    applications = Application.objects.filter(student=user).count()

    return render(request, 'profiles/view.html', {
        'profile': profile,
        'profile_user': user,
        'achievements': achievements,
        'posts': posts,
        'applications_count': applications,
        'is_own_profile': is_own_profile,
        'form': form,
        'user_form': user_form,
    })


@login_required
def my_profile(request):
    """Redirect to own profile page."""
    return redirect('profile_view', username=request.user.username)


def leaderboard(request):
    """Top students ranked by InCoScore."""
    profiles = StudentProfile.objects.filter(
        incoscore__gt=0
    ).order_by('-incoscore').select_related('user')[:50]
    return render(request, 'profiles/leaderboard.html', {'profiles': profiles})
