from django.db import models
import qrcode
from django.contrib.auth.models import User
from io import BytesIO

from django.core.files import File
from django.urls import reverse
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from datetime import timedelta
from urllib.parse import urlencode


class EventCategory(models.Model):
    category_name = models.CharField(max_length=100)
    category_code = models.CharField(max_length=20, unique=True)
    priority = models.PositiveIntegerField()

    def __str__(self):
        return self.category_name


class Event(models.Model):

    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    event_name = models.CharField(max_length=100)
    event_code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    description = models.TextField()
    venue = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    max_participants = models.PositiveIntegerField()

    banner = models.ImageField(
        upload_to="event_banners/",
        blank=True,
        null=True,
    )

    event_qr_code = models.ImageField(
        upload_to="event_qr_codes/",
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Upcoming'
    )

    def __str__(self):
        return self.event_name

    @property
    def google_calendar_url(self):
        calendar_end_date = self.end_date + timedelta(days=1)
        query = urlencode({
            "action": "TEMPLATE",
            "text": self.event_name,
            "dates": (
                f"{self.start_date:%Y%m%d}/{calendar_end_date:%Y%m%d}"
            ),
            "details": self.description,
            "location": self.venue,
        })
        return f"https://calendar.google.com/calendar/render?{query}"

    @property
    def google_maps_url(self):
        return (
            "https://www.google.com/maps/search/?api=1&"
            f"{urlencode({'query': self.venue})}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if (
            not self.event_qr_code
            or not self.event_qr_code.storage.exists(self.event_qr_code.name)
        ):
            self.generate_event_qr_code()

    def generate_event_qr_code(self):
        registration_path = reverse(
            "register_event",
            kwargs={"id": self.id},
        )
        registration_url = (
            f"{settings.SITE_URL.rstrip('/')}{registration_path}"
        )
        qr = qrcode.make(registration_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        filename = f"{self.event_name}_{self.id}.png"
        self.event_qr_code.save(
            filename,
            File(buffer),
            save=False,
        )
        super().save(update_fields=["event_qr_code"])

    def delete(self, *args, **kwargs):
        if self.event_qr_code:
            self.event_qr_code.delete(save=False)
        super().delete(*args, **kwargs)


def mark_completed_events():
    today = timezone.localdate()

    completed_count = Event.objects.filter(
        end_date__lt=timezone.localdate(),
    ).exclude(
        status__in=["Completed", "Cancelled"],
    ).update(status="Completed")

    ongoing_count = Event.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        status="Upcoming",
    ).update(status="Ongoing")

    return completed_count + ongoing_count


class EventFeedback(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_feedback_per_user",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} feedback by {self.user}"

from django.db import models
import uuid

class EventMember(models.Model):

    user=models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE
    )

    member_name = models.CharField(max_length=100)

    email = models.EmailField()

    phone = models.CharField(max_length=15)

    joined_date = models.DateField(auto_now_add=True)

    qr_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    qr_code = models.ImageField(
        upload_to="qr_codes/",
        blank=True,
        null=True
    )

    is_checked_in = models.BooleanField(default=False)

    checked_in_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.member_name

    def save(self, *args, **kwargs):

        # Save the object first so qr_token exists
        super().save(*args, **kwargs)

        # Generate QR code only once
        if not self.qr_code:

            try:

                print("Generating QR Code...")

                check_in_path = reverse(
                    "check_in",
                    kwargs={
                        "event_id": self.event_id,
                        "qr_token": self.qr_token,
                    },
                )

                check_in_url = f"{settings.SITE_URL.rstrip('/')}{check_in_path}"

                qr = qrcode.make(check_in_url)

                buffer = BytesIO()

                qr.save(buffer, format="PNG")

                filename = f"{self.member_name}_{self.qr_token}.png"

                self.qr_code.save(
                    filename,
                    File(buffer),
                    save=False
                )

                super().save(update_fields=["qr_code"])

                print("QR Code Saved Successfully!")
                print(self.qr_code.name)

            except Exception as e:

                print("QR Generation Error:", e)
    def delete(self, *args, **kwargs):
        if self.qr_code:
            self.qr_code.delete(save=False)

        super().delete(*args, **kwargs)


class EventWishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_wishlist",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                name="unique_event_wishlist_per_user",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} wishlist: {self.event}"


class SupportRequest(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=200)

    message = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject