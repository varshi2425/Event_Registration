from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
import csv
from .models import (
    EventCategory,
    Event,
    EventMember,
    EventFeedback,
    mark_completed_events,
)
from .forms import EventCategoryForm, EventForm, EventMemberForm, EventFeedbackForm
from django.contrib import messages
from accounts.models import Notification

# ----------------------------
# EVENT CATEGORY
# ----------------------------

def create_category(request):

    if request.method == "POST":

        form = EventCategoryForm(request.POST)

        if form.is_valid():

            category = form.save()

            Notification.objects.create(
                title="Category Created",
                message=f"{category.category_name} category has been created successfully."
            )

            messages.success(
                request,
                "Category created successfully."
            )

            return redirect("category_list")

        else:

            print(form.errors)

    else:

        form = EventCategoryForm()

    return render(
        request,
        "events/create_category.html",
        {
            "form": form
        }
    )


def category_list(request):

    categories = EventCategory.objects.all()

    return render(
        request,
        "events/category_list.html",
        {
            "categories": categories
        }
    )


def edit_category(request, id):

    category = get_object_or_404(
        EventCategory,
        id=id
    )

    if request.method == "POST":

        form = EventCategoryForm(
            request.POST,
            instance=category
        )

        if form.is_valid():

            category = form.save()

            Notification.objects.create(
                title="Category Updated",
                message=f"{category.category_name} category has been updated successfully."
            )

            messages.success(
                request,
                "Category updated successfully."
            )

            return redirect("category_list")

        else:

            print(form.errors)

    else:

        form = EventCategoryForm(
            instance=category
        )

    return render(
        request,
        "events/create_category.html",
        {
            "form": form
        }
    )


def delete_category(request, id):

    category = get_object_or_404(
        EventCategory,
        id=id
    )

    Notification.objects.create(
        title="Category Deleted",
        message=f"{category.category_name} category has been deleted successfully."
    )

    category.delete()

    messages.success(
        request,
        "Category deleted successfully."
    )

    return redirect("category_list")


# ----------------------------
# EVENT
# ----------------------------

def create_event(request):

    if request.method == "POST":

        form = EventForm(request.POST, request.FILES)

        if form.is_valid():

            event = form.save()

            Notification.objects.create(
                title="New Event Created",
                message=f"{event.event_name} has been created successfully."
            )

            messages.success(
                request,
                "Event added successfully."
            )

            return redirect("event_list")

        else:

            print(form.errors)

    else:

        form = EventForm()

    return render(
        request,
        "events/create_event.html",
        {
            "form": form
        }
    )

def event_list(request):

    mark_completed_events()
    events = Event.objects.all()

    return render(
        request,
        "events/event_list.html",
        {
            "events": events,
            "is_staff": request.user.is_staff
        }
    )


@login_required
def feedback_list(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to view feedback.")
        return redirect("user_dashboard")

    feedback = EventFeedback.objects.select_related(
        "event",
        "user",
    ).order_by("-created_at")

    return render(
        request,
        "admin/feedback_list.html",
        {"feedback": feedback},
    )


def event_details(request, id):

    mark_completed_events()
    event = get_object_or_404(
        Event,
        id=id
    )

    feedback_form = None
    if request.user.is_authenticated and not request.user.is_staff:
        feedback_form = EventFeedbackForm(
            instance=EventFeedback.objects.filter(
                event=event,
                user=request.user,
            ).first()
        )

    return render(
        request,
        "events/event_details.html",
        {
            "event": event,
            "feedback": event.feedback.select_related("user"),
            "feedback_form": feedback_form,
        }
    )


@login_required
def submit_feedback(request, id):
    event = get_object_or_404(Event, id=id)

    if request.user.is_staff:
        return redirect("event_details", id=event.id)

    if not EventMember.objects.filter(user=request.user, event=event).exists():
        messages.error(request, "Register for this event before leaving feedback.")
        return redirect("event_details", id=event.id)

    if request.method != "POST":
        return redirect("event_details", id=event.id)

    form = EventFeedbackForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "events/event_details.html",
            {
                "event": event,
                "feedback": event.feedback.select_related("user"),
                "feedback_form": form,
            },
            status=400,
        )

    EventFeedback.objects.update_or_create(
        event=event,
        user=request.user,
        defaults={
            "rating": form.cleaned_data["rating"],
            "comment": form.cleaned_data["comment"],
        },
    )
    messages.success(request, "Your feedback was saved.")

    return redirect("event_details", id=event.id)

@login_required
def edit_event(request, id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to edit events."
        )
        return redirect(
            "event_details",
            id=id
        )

    event = get_object_or_404(
        Event,
        id=id
    )

    if request.method == "POST":

        form = EventForm(
            request.POST,
            request.FILES,
            instance=event
        )

        if form.is_valid():

            event = form.save()

            Notification.objects.create(
                title="Event Updated",
                message=f"{event.event_name} has been updated successfully."
            )

            messages.success(
                request,
                "Event updated successfully."
            )

            return redirect("event_list")

        else:

            print(form.errors)

    else:

        form = EventForm(
            instance=event
        )

    return render(
        request,
        "events/edit_event.html",
        {
            "form": form,
            "event": event
        }
    )


def delete_event(request, id):

    event = get_object_or_404(
        Event,
        id=id
    )

    if request.method == "POST":

        Notification.objects.create(
            title="Event Deleted",
            message=f"{event.event_name} has been deleted successfully."
        )

        event.delete()

        messages.success(
            request,
            "Event deleted successfully."
        )

        return redirect("event_list")

    return render(
        request,
        "events/delete_event.html",
        {
            "event": event
        }
    )


# ----------------------------
# EVENT MEMBERS
# ----------------------------

def add_event_member(request):

    if request.method == "POST":

        form = EventMemberForm(request.POST)

        if form.is_valid():

            member = form.save()

            Notification.objects.create(
                title="New Member Registered",
                message=f"{member.member_name} has registered for {member.event.event_name}."
            )

            messages.success(
                request,
                "Member registered successfully."
            )

            return redirect("member_list")

        else:

            print(form.errors)

    else:

        form = EventMemberForm()

    return render(
        request,
        "events/add_member.html",
        {
            "form": form
        }
    )


from .models import EventMember

def member_list(request):
    members = EventMember.objects.all()

    total_members = members.count()
    checked_in = members.filter(is_checked_in=True).count()
    pending = members.filter(is_checked_in=False).count()

    context = {
        "members": members,
        "total_members": total_members,
        "checked_in": checked_in,
        "pending": pending,
    }

    return render(request, "events/member_list.html", context)

def edit_member(request, id):

    member = get_object_or_404(
        EventMember,
        id=id
    )

    if request.method == "POST":

        form = EventMemberForm(
            request.POST,
            instance=member
        )

        if form.is_valid():

            member = form.save()

            Notification.objects.create(
                title="Member Updated",
                message=f"{member.member_name}'s registration has been updated."
            )

            messages.success(
                request,
                "Member updated successfully."
            )

            return redirect("member_list")

        else:

            print(form.errors)

    else:

        form = EventMemberForm(
            instance=member
        )

    return render(
        request,
        "events/edit_member.html",
        {
            "form": form,
            "member": member
        }
    )

def delete_member(request, id):

    member = get_object_or_404(
        EventMember,
        id=id
    )

    if request.method == "POST":

        # Delete QR image from media folder
        if member.qr_code:
            member.qr_code.delete(save=False)

        Notification.objects.create(
            title="Member Removed",
            message=f"{member.member_name} has been removed from {member.event.event_name}."
        )

        member.delete()

        messages.success(
            request,
            "Member deleted successfully."
        )

        return redirect("member_list")

    return render(
        request,
        "events/delete_member.html",
        {
            "member": member
        }
    )

from .models import SupportRequest
def contact_support(request):

    requests = SupportRequest.objects.all()

    return render(
        request,
        'admin/contact_support.html',
        {
            'requests': requests
        }
    )

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db import transaction
from .models import EventMember

@login_required
def check_in(request, event_id, qr_token):

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to check in members."
        )
        return redirect("user_dashboard")

    event = get_object_or_404(
        Event,
        id=event_id
    )

    with transaction.atomic():
        member = get_object_or_404(
            EventMember.objects.select_for_update(),
            qr_token=qr_token
        )

        # Make sure the QR belongs to the selected event
        if member.event.id != event.id:

            messages.error(
                request,
                "This QR code does not belong to this event."
            )

            return redirect(
                "qr_scanner",
                event_id=event.id
            )

        already_checked = member.is_checked_in

        if not already_checked:

            member.is_checked_in = True
            member.checked_in_at = timezone.now()
            member.save(update_fields=["is_checked_in", "checked_in_at"])

    return render(
        request,
        "events/check_in_success.html",
        {
            "member": member,
            "already_checked": already_checked,
        },
    )

from django.contrib.auth.decorators import login_required
@login_required
def register_event(request, id):

    mark_completed_events()
    event = get_object_or_404(
        Event,
        id=id
    )

    # Completed or cancelled events cannot be registered
    if event.status in ["Completed", "Cancelled"]:

        messages.error(
            request,
            f"Registration for {event.event_name} is closed."
        )

        return redirect(
            "event_details",
            id=event.id
        )

    # Check if user already registered
    already_registered = EventMember.objects.filter(
        user=request.user,
        event=event
    ).exists()

    if already_registered:

        messages.info(
            request,
            "You have already registered for this event."
        )

        return redirect(
            "user_dashboard"
        )

    # Check maximum participants
    registered_count = EventMember.objects.filter(
        event=event
    ).count()

    if registered_count >= event.max_participants:

        messages.error(
            request,
            "Sorry, this event has reached its maximum participant limit."
        )

        return redirect(
            "event_details",
            id=event.id
        )

    if request.method == "POST":

        member_name = request.POST.get("member_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()

        # Validate fields
        if not member_name or not email or not phone:

            messages.error(
                request,
                "Please fill in all the required fields."
            )

            return render(
                request,
                "events/register_event.html",
                {
                    "event": event,
                    "member_name": member_name,
                    "email": email,
                    "phone": phone,
                }
            )

        # Create registration
        EventMember.objects.create(

            user=request.user,

            event=event,

            member_name=member_name,

            email=email,

            phone=phone
        )

        Notification.objects.create(
            title="Event Registration Successful",
            message=(
                f"{request.user.username} registered "
                f"for {event.event_name}."
            )
        )

        send_mail(
            subject=f"Registration confirmed: {event.event_name}",
            message=(
                f"Hello {member_name},\n\n"
                f"Your registration for {event.event_name} is confirmed.\n"
                f"Date: {event.start_date} to {event.end_date}\n"
                f"Venue: {event.venue}\n\n"
                "Please keep your attendee QR code available for check-in."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

        messages.success(
            request,
            f"You have successfully registered for "
            f"{event.event_name}."
        )

        return redirect("user_dashboard")

    return render(
        request,
        "events/register_event.html",
        {
            "event": event,
        }
    )


@login_required
def my_qr_codes(request):

    registrations = EventMember.objects.filter(
        user=request.user
    ).select_related(
        "event",
        "event__category",
    ).order_by(
        "-event__start_date"
    )

    return render(
        request,
        "events/my_qr_codes.html",
        {
            "registrations": registrations,
        }
    )


@login_required
def qr_scanner(request, event_id):

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to scan QR codes."
        )
        return redirect("user_dashboard")

    event = get_object_or_404(Event, id=event_id)

    return render(
        request,
        "events/qr_scanner.html",
        {
            "event": event,
        }
    )


@login_required
def qr_scanner_home(request):

    if not request.user.is_staff:
        messages.error(
            request,
            "You do not have permission to scan QR codes."
        )
        return redirect("user_dashboard")

    mark_completed_events()
    events = Event.objects.exclude(
        status__in=["Completed", "Cancelled"]
    ).order_by("start_date", "event_name")

    return render(
        request,
        "events/qr_scanner_home.html",
        {
            "events": events,
        }
    )


@login_required
def cancel_registration(request, id):
    registration = get_object_or_404(
        EventMember,
        id=id,
        user=request.user,
    )

    if request.method == "POST":
        event_name = registration.event.event_name
        registration.delete()
        Notification.objects.create(
            user=request.user,
            title="Registration Cancelled",
            message=f"Your registration for {event_name} was cancelled.",
        )
        messages.success(request, f"Your registration for {event_name} was cancelled.")

    return redirect("my_registrations")


@login_required
def export_attendance(request):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to export attendance.")
        return redirect("user_dashboard")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance.csv"'
    writer = csv.writer(response)
    writer.writerow(["Event", "Member", "Email", "Phone", "Registered", "Checked In", "Checked In At"])

    for member in EventMember.objects.select_related("event").order_by("event__start_date", "member_name"):
        writer.writerow([
            member.event.event_name,
            member.member_name,
            member.email,
            member.phone,
            member.joined_date,
            "Yes" if member.is_checked_in else "No",
            member.checked_in_at or "",
        ])

    return response