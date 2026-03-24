from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import Opportunity, ScrapingLog, DOMAIN_CHOICES, OPPORTUNITY_TYPES


def home(request):
    """Landing page with stats and featured opportunities."""
    featured = Opportunity.objects.filter(is_active=True)[:6]
    stats = {
        'total': Opportunity.objects.filter(is_active=True).count(),
        'universities': Opportunity.objects.values('university').distinct().count(),
        'domains': len(DOMAIN_CHOICES),
    }
    return render(request, 'opportunities/home.html', {
        'featured': featured,
        'stats': stats,
    })


@login_required
def dashboard(request):
    """
    Personalized opportunity dashboard.
    Shows opportunities matching the student's domain interests.
    Falls back to all if no profile domains set.
    """
    from apps.profiles.models import StudentProfile
    try:
        profile = request.user.studentprofile
        domains = profile.domains_of_interest or []
    except StudentProfile.DoesNotExist:
        domains = []

    no_domains_set = False
    if not domains:
        no_domains_set = True
        opportunities = Opportunity.objects.none()
    else:
        opportunities = Opportunity.objects.filter(is_active=True).filter(domain__in=domains)

    # Search
    q = request.GET.get('q', '')
    if q:
        opportunities = opportunities.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q)
        )

    # Domain filter from URL
    domain_filter = request.GET.get('domain', '')
    if domain_filter:
        opportunities = opportunities.filter(domain=domain_filter)

    # Type filter
    type_filter = request.GET.get('type', '')
    if type_filter:
        opportunities = opportunities.filter(opportunity_type=type_filter)

    # University filter
    uni_filter = request.GET.get('university', '')
    if uni_filter:
        opportunities = opportunities.filter(university=uni_filter)

    paginator = Paginator(opportunities, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'opportunities/dashboard.html', {
        'page_obj': page_obj,
        'domain_choices': DOMAIN_CHOICES,
        'type_choices': OPPORTUNITY_TYPES,
        'q': q,
        'domain_filter': domain_filter,
        'type_filter': type_filter,
        'user_domains': domains,
        'no_domains_set': no_domains_set,
    })


def opportunity_list(request):
    """Public listing of all opportunities with filters."""
    opportunities = Opportunity.objects.filter(is_active=True)

    q = request.GET.get('q', '')
    if q:
        opportunities = opportunities.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )

    domain_filter = request.GET.get('domain', '')
    if domain_filter:
        opportunities = opportunities.filter(domain=domain_filter)

    type_filter = request.GET.get('type', '')
    if type_filter:
        opportunities = opportunities.filter(opportunity_type=type_filter)

    paginator = Paginator(opportunities, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'opportunities/list.html', {
        'page_obj': page_obj,
        'domain_choices': DOMAIN_CHOICES,
        'type_choices': OPPORTUNITY_TYPES,
        'q': q,
        'domain_filter': domain_filter,
        'type_filter': type_filter,
    })


def opportunity_detail(request, pk):
    """Full detail page for a single opportunity."""
    opportunity = get_object_or_404(Opportunity, pk=pk)
    similar = Opportunity.objects.filter(
        domain=opportunity.domain,
        is_active=True
    ).exclude(pk=pk)[:4]

    user_applied = False
    if request.user.is_authenticated:
        from apps.applications.models import Application
        user_applied = Application.objects.filter(
            student=request.user, opportunity=opportunity
        ).exists()

    return render(request, 'opportunities/detail.html', {
        'opportunity': opportunity,
        'similar': similar,
        'user_applied': user_applied,
    })


@login_required
def trigger_scrape(request):
    """Admin-only manual trigger for scraping. POST only."""
    if not request.user.is_staff:
        messages.error(request, "Only staff can trigger scraping.")
        return redirect('dashboard')

    if request.method == 'POST':
        from .tasks import scrape_all_universities
        scrape_all_universities.delay()
        messages.success(request, "Scraping started in background! Check back in a few minutes.")

    return redirect('dashboard')


def api_opportunities(request):
    """REST API endpoint returning opportunities as JSON."""
    opportunities = Opportunity.objects.filter(is_active=True).values(
        'id', 'title', 'university', 'domain', 'opportunity_type',
        'deadline', 'source_url', 'location', 'scraped_at'
    )[:50]
    return JsonResponse({'results': list(opportunities)})
