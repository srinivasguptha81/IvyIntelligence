from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Achievement, ScoreHistory, ACHIEVEMENT_CATEGORIES
from .engine import update_student_score, get_score_breakdown, get_leaderboard, get_recommendations


@login_required
def incoscore_dashboard(request):
    """Personal InCoScore dashboard with breakdown and history."""
    profile = request.user.studentprofile
    achievements = Achievement.objects.filter(student=profile)
    verified_achievements = achievements.filter(verified=True)
    history = ScoreHistory.objects.filter(student=profile)[:10]
    breakdown = get_score_breakdown(profile)
    recommendations = get_recommendations(profile)

    # Recalculate on each visit (lightweight operation)
    update_student_score(profile, reason="Dashboard visit")

    return render(request, 'incoscore/dashboard.html', {
        'profile': profile,
        'achievements': achievements,
        'verified_count': verified_achievements.count(),
        'pending_count': achievements.filter(verified=False).count(),
        'history': history,
        'breakdown': breakdown,
        'recommendations': recommendations,
        'categories': ACHIEVEMENT_CATEGORIES,
    })


@login_required
def add_achievement(request):
    """Submit a new achievement for verification."""
    if request.method == 'POST':
        profile = request.user.studentprofile
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category')
        description = request.POST.get('description', '')
        proof_url = request.POST.get('proof_url', '')
        proof_file = request.FILES.get('proof_file')
        achieved_on = request.POST.get('achieved_on') or None

        if not title or not category:
            messages.error(request, "Title and category are required.")
            return redirect('incoscore_dashboard')

        Achievement.objects.create(
            student=profile,
            title=title,
            category=category,
            description=description,
            proof_url=proof_url,
            proof_file=proof_file,
            achieved_on=achieved_on,
            verified=False,  # Requires admin verification
        )
        messages.success(request, "Achievement submitted! It will be visible after verification.")

    return redirect('incoscore_dashboard')


@login_required
def delete_achievement(request, achievement_id):
    """Delete an unverified achievement."""
    achievement = get_object_or_404(Achievement, pk=achievement_id, student=request.user.studentprofile)
    if achievement.verified:
        messages.error(request, "Cannot delete a verified achievement.")
    else:
        achievement.delete()
        messages.success(request, "Achievement removed.")
    return redirect('incoscore_dashboard')


def global_leaderboard(request):
    """Public leaderboard of top students by InCoScore."""
    top_students = get_leaderboard(limit=100)
    return render(request, 'incoscore/leaderboard.html', {
        'top_students': top_students,
    })


@login_required
def api_my_score(request):
    """JSON API endpoint for current user's InCoScore and breakdown."""
    profile = request.user.studentprofile
    breakdown = get_score_breakdown(profile)
    return JsonResponse({
        'username': request.user.username,
        'incoscore': profile.incoscore,
        'breakdown': breakdown,
    })
