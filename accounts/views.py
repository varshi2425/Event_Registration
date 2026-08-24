from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout , update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import events
from events.models import EventCategory, Event, EventMember, EventWishlist, mark_completed_events
from .models import Profile, SupportRequest, Customization ,Notification
from .forms import UserUpdateForm, ProfileUpdateForm, SupportForm, CustomizationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count
from django.core.paginator import Paginator
from datetime import date, timedelta
import json

USER_EVENT_NOTIFICATION_TITLES = [
    "New Event Created",
    "Event Updated",
]


def cleanup_notifications():
    Notification.delete_expired()

# Signup

def signup_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")


        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "accounts/signup.html"
            )


        user = User.objects.create_user(
            username=username,
            password=password
        )


        # Create profile for new user
        Profile.objects.get_or_create(
            user=user
        )


        messages.success(
            request,
            "Account created successfully. Please login."
        )

        return redirect("login")


    return render(
        request,
        "accounts/signup.html"
    )



# Login

def login_view(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']


        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            Profile.objects.get_or_create(user=user)

            if user.is_staff:
                return redirect("admin_dashboard")

            return redirect("user_dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# Logout

def logout_view(request):

    logout(request)

    return redirect("login")


# Admin Dashboard

@login_required
def admin_dashboard(request):

    if not request.user.is_staff:
        return redirect("user_dashboard")

    cleanup_notifications()
    mark_completed_events()

    profile, _ = Profile.objects.get_or_create(user=request.user)
    customization, created = Customization.objects.get_or_create(id=1)

    if request.method == "POST":
        form = CustomizationForm(request.POST, instance=customization)
        if form.is_valid():
            form.save()
            messages.success(request, "Customization saved successfully.")
            return redirect("admin_dashboard")
    else:
        form = CustomizationForm(instance=customization)

    notifications = Notification.objects.order_by("-created_at")[:5]
    unread_count = Notification.objects.filter(is_read=False).count()
    events = Event.objects.annotate(member_count=Count("eventmember"))
    event_labels = json.dumps([event.event_name for event in events])
    member_counts = json.dumps([event.member_count for event in events])

    colors = ["#4F46E5", "#10B981", "#F59E0B", "#EC4899", "#06B6D4", "#8B5CF6"]
    calendar_events = []
    for index, event in enumerate(Event.objects.all()):
        calendar_events.append({
            "title": event.event_name,
            "start": event.start_date.strftime("%Y-%m-%d"),
            "backgroundColor": colors[index % len(colors)],
            "borderColor": colors[index % len(colors)],
        })

    today = date.today()
    context = {
        "profile": profile,
        "category_count": EventCategory.objects.count(),
        "event_count": Event.objects.count(),
        "member_count": EventMember.objects.count(),
        "upcoming_events": Event.objects.filter(start_date__gt=today).count(),
        "ongoing_events": Event.objects.filter(start_date__lte=today, end_date__gte=today).count(),
        "completed_events": Event.objects.filter(end_date__lt=today).count(),
        "checked_in_members": EventMember.objects.filter(is_checked_in=True).count(),
        "customization": customization,
        "form": form,
        "notifications": notifications,
        "unread_count": unread_count,
        "event_labels": event_labels,
        "member_counts": member_counts,
        "calendar_events": json.dumps(calendar_events),
    }

    return render(request, "admin/admin_dashboard.html", context)
    checked_in_members = EventMember.objects.filter(
        is_checked_in=True
    ).count()

    # ---------------- Context ----------------

    context = {

        # Summary Cards
        "category_count": EventCategory.objects.count(),

        "event_count": Event.objects.count(),

        "member_count": EventMember.objects.count(),

        # Event Status
        "upcoming_events": upcoming_events,

        "ongoing_events": ongoing_events,

        "completed_events": completed_events,

        "checked_in_members": checked_in_members,

        # Customization
        "customization": customization,

        "form": form,

        # Notifications
        "notifications": notifications,

        "unread_count": unread_count,

        # Analytics
        "event_labels": event_labels,

        "member_counts": member_counts,

        # Calendar
        "calendar_events": json.dumps(calendar_events),

    }

    return render(
        request,
        "admin/admin_dashboard.html",
        context
    )

# User Dashboard

from django.utils import timezone
from django.db.models import Q

@login_required
def user_dashboard(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user
    )


    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')


    # -----------------------------------
    # USER'S REGISTERED EVENTS
    # -----------------------------------

    user_registrations = EventMember.objects.filter(
        user=request.user
    ).values_list(
        'event',
        flat=True
    )

    registered_events = Event.objects.filter(
        id__in=user_registrations
    ).order_by('-start_date')


    # -----------------------------------
    # ALL EVENTS
    # -----------------------------------

    all_events = Event.objects.all()


    # -----------------------------------
    # SEARCH
    # -----------------------------------

    if search_query:

        all_events = all_events.filter(

            Q(event_name__icontains=search_query) |

            Q(event_code__icontains=search_query) |

            Q(description__icontains=search_query) |

            Q(venue__icontains=search_query) |

            Q(category__category_name__icontains=search_query)

        )


    # -----------------------------------
    # CATEGORY FILTER
    # -----------------------------------

    if category_filter:

        all_events = all_events.filter(
            category__id=category_filter
        )


    # -----------------------------------
    # STATUS FILTER
    # -----------------------------------

    if status_filter:

        all_events = all_events.filter(
            status=status_filter
        )


    # -----------------------------------
    # UPCOMING & PAST REGISTERED EVENTS
    # -----------------------------------

    today = timezone.now().date()

    upcoming_events = registered_events.filter(
        start_date__gte=today
    ).order_by(
        'start_date'
    )

    past_events = registered_events.filter(
        start_date__lt=today
    ).order_by(
        '-start_date'
    )


    # -----------------------------------
    # STATISTICS
    # -----------------------------------

    total_events = Event.objects.count()

    user_registrations_count = user_registrations.count()

    total_categories = EventCategory.objects.count()

    upcoming_count = upcoming_events.count()

    past_count = past_events.count()


    # -----------------------------------
    # CATEGORIES
    # -----------------------------------

    categories = EventCategory.objects.all()


    # -----------------------------------
    # EVENT STATUSES
    # -----------------------------------

    event_statuses = Event.objects.values_list(
        'status',
        flat=True
    ).distinct()


    # -----------------------------------
    # CONTEXT
    # -----------------------------------

    context = {

        "profile": profile,

        "registered_events": registered_events[:5],

        "upcoming_events": upcoming_events[:3],

        "past_events": past_events[:3],

        "all_events": all_events,

        "total_events": total_events,

        "user_registrations_count": user_registrations_count,

        "total_categories": total_categories,

        "upcoming_count": upcoming_count,

        "past_count": past_count,

        "categories": categories,

        "event_statuses": event_statuses,

        "search_query": search_query,

        "category_filter": category_filter,

        "status_filter": status_filter,

    }


    return render(
        request,
        "user/user_dashboard.html",
        context
    )





# User page views

@login_required
def user_dashboard(request):
    cleanup_notifications()
    mark_completed_events()
    profile, _ = Profile.objects.get_or_create(user=request.user)
    registrations = EventMember.objects.filter(user=request.user)
    today = timezone.now().date()
    customization, _ = Customization.objects.get_or_create(
        user=request.user,
        defaults={"dashboard_title": "User Dashboard"},
    )

    if request.method == "POST":
        form = CustomizationForm(request.POST, instance=customization)
        if form.is_valid():
            form.save()
            messages.success(request, "Dashboard customization saved.")
            return redirect("user_dashboard")
    else:
        form = CustomizationForm(instance=customization)

    notifications = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        title__in=USER_EVENT_NOTIFICATION_TITLES,
    ).order_by("-created_at")[:5]
    unread_count = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        title__in=USER_EVENT_NOTIFICATION_TITLES,
        is_read=False,
    ).count()

    calendar_events = []
    colors = ["#0d6efd", "#198754", "#fd7e14", "#6f42c1", "#20c997"]
    for index, event in enumerate(Event.objects.all()):
        calendar_events.append({
            "title": event.event_name,
            "start": event.start_date.strftime("%Y-%m-%d"),
            "end": (event.end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "url": reverse("event_details", kwargs={"id": event.id}),
            "backgroundColor": colors[index % len(colors)],
            "borderColor": colors[index % len(colors)],
        })

    return render(
        request,
        "user/user_dashboard_summary.html",
        {
            "profile": profile,
            "total_events": Event.objects.count(),
            "total_categories": EventCategory.objects.count(),
            "user_registrations_count": registrations.count(),
            "upcoming_count": registrations.filter(
                event__start_date__gte=today
            ).count(),
            "past_count": registrations.filter(
                event__start_date__lt=today
            ).count(),
            "categories": EventCategory.objects.all(),
            "event_statuses": Event.objects.values_list(
                "status", flat=True
            ).distinct(),
            "customization": customization,
            "form": form,
            "notifications": notifications,
            "unread_count": unread_count,
            "calendar_events": json.dumps(calendar_events),
        },
    )


@login_required
def user_calendar(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    customization, _ = Customization.objects.get_or_create(
        user=request.user,
        defaults={"dashboard_title": "User Dashboard"},
    )
    calendar_events = []
    colors = ["#0d6efd", "#198754", "#fd7e14", "#6f42c1", "#20c997"]

    for index, event in enumerate(Event.objects.all()):
        calendar_events.append({
            "title": event.event_name,
            "start": event.start_date.strftime("%Y-%m-%d"),
            "end": (event.end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "url": reverse("event_details", kwargs={"id": event.id}),
            "backgroundColor": colors[index % len(colors)],
            "borderColor": colors[index % len(colors)],
        })

    return render(
        request,
        "user/user_calendar.html",
        {
            "profile": profile,
            "customization": customization,
            "calendar_events": json.dumps(calendar_events),
        },
    )


@login_required
def user_events(request):
    missing_qr_events = Event.objects.filter(
        Q(event_qr_code__isnull=True) | Q(event_qr_code="")
    )
    for event in missing_qr_events:
        event.generate_event_qr_code()

    events = Event.objects.annotate(
        registered_count=Count("eventmember")
    ).select_related("category")
    search_query = request.GET.get("search", "").strip()
    category_filter = request.GET.get("category", "")
    status_filter = request.GET.get("status", "")

    if search_query:
        events = events.filter(
            Q(event_name__icontains=search_query)
            | Q(event_code__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(venue__icontains=search_query)
            | Q(category__category_name__icontains=search_query)
        )

    if category_filter:
        events = events.filter(category_id=category_filter)

    if status_filter:
        events = events.filter(status=status_filter)

    registered_event_ids = EventMember.objects.filter(
        user=request.user
    ).values_list("event_id", flat=True)
    wishlist_event_ids = EventWishlist.objects.filter(
        user=request.user
    ).values_list("event_id", flat=True)

    paginator = Paginator(
        events.order_by("start_date", "event_name"),
        6,
    )
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "events/user_events.html",
        {
            "events": page_obj,
            "page_obj": page_obj,
            "event_count": paginator.count,
            "categories": EventCategory.objects.all(),
            "event_statuses": Event.objects.values_list(
                "status", flat=True
            ).distinct(),
            "registered_event_ids": registered_event_ids,
            "wishlist_event_ids": wishlist_event_ids,
            "search_query": search_query,
            "category_filter": category_filter,
            "status_filter": status_filter,
        },
    )


@login_required
def my_registrations(request):
    registrations = EventMember.objects.filter(
        user=request.user
    ).select_related("event", "event__category")
    today = timezone.now().date()

    return render(
        request,
        "events/my_registrations.html",
        {
            "upcoming_registrations": registrations.filter(
                event__start_date__gte=today
            ).order_by("event__start_date"),
            "past_registrations": registrations.filter(
                event__start_date__lt=today
            ).order_by("-event__start_date"),
        },
    )


# Profile

@login_required
def profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # Use different template based on user role
    template = "admin/profile.html" if request.user.is_staff else "user/profile.html"

    return render(
        request,
        template,
        {
            "profile": profile,
            "is_staff": request.user.is_staff
        }
    )



# Edit Profile

@login_required
def edit_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )


    if request.method == "POST":

        user_form = UserUpdateForm(
            request.POST,
            instance=request.user
        )


        profile_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=profile
        )


        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()

            profile_form.save()


            messages.success(
                request,
                "Profile updated successfully."
            )

            # Redirect to appropriate dashboard based on user role
            if request.user.is_staff:
                return redirect("profile")
            else:
                return redirect("user_dashboard")


    else:

        user_form = UserUpdateForm(
            instance=request.user
        )


        profile_form = ProfileUpdateForm(
            instance=profile
        )

    # Use different template based on user role
    template = "admin/edit_profile.html" if request.user.is_staff else "user/edit_profile.html"

    return render(
        request,
        template,
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "is_staff": request.user.is_staff
        }
    )



# Contact Support

@login_required
def contact_support(request):

    # Show all requests for admins, only user's requests for regular users
    if request.user.is_staff:
        support_requests = SupportRequest.objects.all()
        template = "admin/contact_support.html"
    else:
        support_requests = SupportRequest.objects.filter(
            email=request.user.email
        )
        template = "user/contact_support.html"


    return render(
        request,
        template,
        {
            "requests": support_requests,
            "is_staff": request.user.is_staff
        }
    )



# Update Support Status

@login_required
def update_support_status(request, id):

    support_request = get_object_or_404(
        SupportRequest,
        id=id
    )


    if request.method == "POST":

        support_request.status = request.POST.get(
            "status"
        )

        support_request.save()


    return redirect(
        "contact_support"
    )

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def mark_notifications_read(request):
    cleanup_notifications()

    if request.user.is_staff:
        Notification.objects.filter(is_read=False).update(is_read=True)
    else:
        Notification.objects.filter(
            Q(user=request.user) | Q(user__isnull=True),
            title__in=USER_EVENT_NOTIFICATION_TITLES,
            is_read=False,
        ).update(is_read=True)

    return JsonResponse({
        "status": "success"
    })


@login_required
@require_POST
def chatbot_reply(request):

    message = request.POST.get("message", "").strip().lower()

    if not message:
        return JsonResponse({
            "reply": "Please enter a question about events, registration, or check-in."
        }, status=400)

    if any(word in message for word in ["hello", "hi", "hey"]):
        reply = "Hello! I can help with events, registration, QR check-in, and support."
    elif "register" in message or "registration" in message or "join" in message:
        reply = "Open Events, choose an upcoming event, and select Register. Your registration will appear under My Registrations."
    elif "qr" in message or "check in" in message or "check-in" in message:
        reply = "Administrators can open an event and choose Scan Attendance. Allow camera access, then scan the member QR code."
    elif "event" in message:
        reply = "You can browse events from the Events page and filter them by category or status from the user dashboard."
    elif "support" in message or "help" in message:
        reply = "Please use Contact Support to send a request. An administrator can update its status there."
    else:
        reply = "I can help with event registration, events, QR check-in, and support. Try asking about one of those."

    return JsonResponse({"reply": reply})

@login_required
def notification_list(request):
    cleanup_notifications()

    if request.user.is_staff:
        notifications = Notification.objects.order_by("-created_at")
        template = "admin/notifications.html"
    else:
        notifications = Notification.objects.filter(
            Q(user=request.user) | Q(user__isnull=True),
            title__in=USER_EVENT_NOTIFICATION_TITLES,
        ).order_by("-created_at")
        template = "user/notifications.html"

    return render(
        request,
        template,
        {
            "notifications": notifications
        }
    )

def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(request, user)

            messages.success(
                request,
                "Password changed successfully!"
            )

            return redirect("profile")

    else:

        form = PasswordChangeForm(request.user)

    return render(
        request,
        "accounts/change_password.html",
        {"form": form}
    )

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Customization

@login_required
def reset_customization(request):

    if request.user.is_staff:
        customization = Customization.objects.get(id=1)
        redirect_target = "admin_dashboard"
    else:
        customization, _ = Customization.objects.get_or_create(
            user=request.user,
            defaults={"dashboard_title": "User Dashboard"},
        )
        redirect_target = "user_dashboard"

    customization.dashboard_title = (
        "Admin Dashboard" if request.user.is_staff else "User Dashboard"
    )
    customization.theme = "light"
    customization.sidebar_color = "#3d4044"
    customization.topbar_color = "#ffffff"
    customization.font_size = "medium"

    customization.save()

    return redirect(redirect_target)