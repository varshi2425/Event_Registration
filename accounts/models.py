from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        default="profile_pictures/default.jpeg"
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.user.username

class SupportRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending','Pending'),
            ('In Progress','In Progress'),
            ('Resolved','Resolved')
        ],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject
    


class Customization(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="dashboard_customization",
    )

    dashboard_title = models.CharField(
        max_length=100,
        default="Admin Dashboard"
    )

    theme = models.CharField(
        max_length=10,
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
        ],
        default="light"
    )

    sidebar_color = models.CharField(
        max_length=7,
        default="#3d4044"
    )

    topbar_color = models.CharField(
        max_length=7,
        default="#ffffff"
    )

    font_size = models.CharField(
        max_length=10,
        choices=[
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
        ],
        default="medium"
    )

    def __str__(self):
        return "Dashboard Customization"

from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @classmethod
    def delete_expired(cls):
        cutoff = timezone.now() - timedelta(hours=24)
        return cls.objects.filter(created_at__lt=cutoff).delete()

    def save(self, *args, **kwargs):
        self.delete_expired()
        super().save(*args, **kwargs)