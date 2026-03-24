from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from .models import Post, Comment, DomainGroup, ChatMessage, DOMAIN_CHOICES


@login_required
def feed(request):
    """Main social feed — shows posts from user's domains and followed groups."""
    try:
        user_domains = request.user.studentprofile.domains_of_interest or []
    except Exception:
        user_domains = []

    posts = Post.objects.filter(is_active=True).select_related('author', 'author__studentprofile')

    # Filter by domain if specified
    domain_filter = request.GET.get('domain', '')
    if domain_filter:
        posts = posts.filter(domain_tag=domain_filter)
    elif user_domains:
        posts = posts.filter(domain_tag__in=user_domains + ['GENERAL'])

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'community/feed.html', {
        'page_obj': page_obj,
        'domain_choices': DOMAIN_CHOICES,
        'domain_filter': domain_filter,
        'groups': DomainGroup.objects.all()[:10],
    })


@login_required
def create_post(request):
    """Create a new community post."""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        domain_tag = request.POST.get('domain_tag', 'GENERAL')
        group_id = request.POST.get('group_id')
        image = request.FILES.get('image')

        if not content:
            messages.error(request, "Post content cannot be empty.")
            return redirect('community_feed')

        post = Post.objects.create(
            author=request.user,
            content=content,
            domain_tag=domain_tag,
            image=image,
        )

        if group_id:
            try:
                post.group = DomainGroup.objects.get(pk=group_id)
                post.save()
            except DomainGroup.DoesNotExist:
                pass

        messages.success(request, "Post shared!")
        return redirect('community_feed')

    return redirect('community_feed')


@login_required
@require_POST
def toggle_like(request, post_id):
    """Toggle like on a post. Returns JSON for AJAX updates."""
    post = get_object_or_404(Post, pk=post_id, is_active=True)
    user = request.user

    if post.likes.filter(pk=user.pk).exists():
        post.likes.remove(user)
        liked = False
    else:
        post.likes.add(user)
        liked = True

    return JsonResponse({'liked': liked, 'count': post.like_count()})


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post."""
    post = get_object_or_404(Post, pk=post_id, is_active=True)
    content = request.POST.get('content', '').strip()

    if content:
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'username': request.user.username,
                'content': comment.content,
                'time': comment.created_at.strftime('%b %d, %Y'),
            })

    return redirect('community_feed')


@login_required
def delete_post(request, post_id):
    """Delete own post."""
    post = get_object_or_404(Post, pk=post_id, author=request.user)
    post.is_active = False
    post.save()
    messages.success(request, "Post deleted.")
    return redirect('community_feed')


def groups_list(request):
    """List all domain groups."""
    groups = DomainGroup.objects.all()
    domain_filter = request.GET.get('domain', '')
    if domain_filter:
        groups = groups.filter(domain=domain_filter)

    return render(request, 'community/groups.html', {
        'groups': groups,
        'domain_choices': DOMAIN_CHOICES,
        'domain_filter': domain_filter,
    })


@login_required
def group_detail(request, group_id):
    """Group detail page with posts and chat."""
    group = get_object_or_404(DomainGroup, pk=group_id)
    posts = Post.objects.filter(group=group, is_active=True)
    recent_messages = ChatMessage.objects.filter(group=group).order_by('-sent_at')[:20]
    is_member = group.members.filter(pk=request.user.pk).exists()

    return render(request, 'community/group_detail.html', {
        'group': group,
        'posts': posts,
        'recent_messages': reversed(list(recent_messages)),
        'is_member': is_member,
    })


@login_required
def join_group(request, group_id):
    """Join or leave a domain group."""
    group = get_object_or_404(DomainGroup, pk=group_id)
    if group.members.filter(pk=request.user.pk).exists():
        group.members.remove(request.user)
        messages.info(request, f"Left {group.name}")
    else:
        group.members.add(request.user)
        messages.success(request, f"Joined {group.name}!")
    return redirect('group_detail', group_id=group_id)
