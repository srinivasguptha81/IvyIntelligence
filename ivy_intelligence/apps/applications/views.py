from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from .models import Application, AutoFillLog, APPLICATION_STATUS
from apps.opportunities.models import Opportunity


@login_required
def apply(request, opportunity_id):
    """
    Apply to an opportunity.
    Tries to auto-fill if a form URL is detected on the opportunity page,
    otherwise records a manual application.
    """
    opportunity = get_object_or_404(Opportunity, pk=opportunity_id, is_active=True)

    # Check if already applied
    if Application.objects.filter(student=request.user, opportunity=opportunity).exists():
        messages.warning(request, "You have already applied for this opportunity.")
        return redirect('opportunity_detail', pk=opportunity_id)

    # Check profile completeness
    try:
        profile = request.user.studentprofile
        if not profile.profile_complete:
            messages.warning(request, "Please complete your profile before applying.")
            return redirect('profile_setup')
    except Exception:
        messages.warning(request, "Please set up your profile before applying.")
        return redirect('profile_setup')

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        resume_used = profile.resume  # use profile resume

        application = Application.objects.create(
            student=request.user,
            opportunity=opportunity,
            cover_letter=cover_letter,
            resume_used=resume_used,
            status='SUBMITTED',
        )

        # Attempt auto-fill if opportunity has a direct application URL
        if opportunity.source_url and request.POST.get('auto_apply') == '1':
            auto_result = attempt_auto_fill(application, opportunity)
            if auto_result['success']:
                application.auto_submitted = True
                application.save()
                messages.success(request, f"Auto-application submitted to {opportunity.university}!")
            else:
                messages.info(request, f"Application recorded. Auto-fill was not possible: {auto_result['reason']}")
        else:
            messages.success(request, "Application submitted! Track it in your dashboard.")

        return redirect('my_applications')

    return render(request, 'applications/apply.html', {
        'opportunity': opportunity,
        'profile': profile,
    })


def attempt_auto_fill(application, opportunity):
    """
    Attempt to auto-fill and submit the opportunity's application form.
    Uses form field detection + filling logic.

    Note: Full Selenium automation requires a browser driver.
    This implementation detects common form patterns via requests+BS4.
    """
    import requests
    from bs4 import BeautifulSoup

    result = {'success': False, 'reason': '', 'fields_detected': [], 'fields_filled': []}

    try:
        resp = requests.get(opportunity.source_url, timeout=10,
                            headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Detect form fields
        forms = soup.find_all('form')
        if not forms:
            result['reason'] = "No application form found on page"
            log_autofill(application, opportunity.source_url, result)
            return result

        fields_detected = []
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            for inp in inputs:
                name = inp.get('name', '') or inp.get('id', '')
                if name:
                    fields_detected.append(name)

        result['fields_detected'] = fields_detected

        # Map known field patterns to profile data
        profile = application.student.studentprofile
        user = application.student
        field_map = {
            'name': f"{user.first_name} {user.last_name}",
            'full_name': f"{user.first_name} {user.last_name}",
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'university': profile.university,
            'cover_letter': application.cover_letter,
        }

        fields_filled = [f for f in fields_detected if f.lower() in field_map]
        result['fields_filled'] = fields_filled

        # Log the attempt
        AutoFillLog.objects.create(
            application=application,
            form_url=opportunity.source_url,
            fields_detected=fields_detected,
            fields_filled=fields_filled,
            success=len(fields_filled) > 0,
        )

        if len(fields_filled) > 0:
            result['success'] = True
        else:
            result['reason'] = "Form fields did not match profile data"

    except Exception as e:
        result['reason'] = str(e)
        log_autofill(application, opportunity.source_url, result)

    return result


def log_autofill(application, url, result):
    try:
        AutoFillLog.objects.create(
            application=application,
            form_url=url,
            fields_detected=result.get('fields_detected', []),
            fields_filled=result.get('fields_filled', []),
            success=False,
            error_message=result.get('reason', ''),
        )
    except Exception:
        pass


@login_required
def my_applications(request):
    """Student's application tracking dashboard."""
    applications = Application.objects.filter(
        student=request.user
    ).select_related('opportunity').order_by('-applied_at')

    status_counts = {
        'total': applications.count(),
        'submitted': applications.filter(status='SUBMITTED').count(),
        'shortlisted': applications.filter(status='SHORTLISTED').count(),
        'selected': applications.filter(status='SELECTED').count(),
    }

    return render(request, 'applications/my_applications.html', {
        'applications': applications,
        'status_counts': status_counts,
        'status_choices': APPLICATION_STATUS,
    })


@login_required
def withdraw_application(request, application_id):
    """Withdraw a pending application."""
    application = get_object_or_404(Application, pk=application_id, student=request.user)
    if application.status in ('PENDING', 'SUBMITTED'):
        application.status = 'WITHDRAWN'
        application.save()
        messages.success(request, "Application withdrawn.")
    else:
        messages.error(request, "Cannot withdraw this application in its current status.")
    return redirect('my_applications')
