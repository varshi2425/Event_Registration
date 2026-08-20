from django import forms
from .models import EventCategory


class EventCategoryForm(forms.ModelForm):

    class Meta:
        model = EventCategory

        fields = [
            "category_name",
            "category_code",
            "priority"
        ]

        widgets = {
            "category_name": forms.TextInput(attrs={"class": "form-control"}),
            "category_code": forms.TextInput(attrs={"class": "form-control"}),
            "priority": forms.NumberInput(attrs={"class": "form-control"}),
        }

from .models import Event, EventFeedback


class EventForm(forms.ModelForm):

    class Meta:
        model = Event

        fields = [
            "event_name",
            "event_code",
            "category",
            "description",
            "venue",
            "start_date",
            "end_date",
            "max_participants",
            "status",
            "banner",
        ]

        widgets = {

            "event_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "event_code": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "category": forms.Select(
                attrs={"class": "form-select"}
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "venue": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "max_participants": forms.NumberInput(
                attrs={"class": "form-control"}
            ),

            "status": forms.Select(
                attrs={"class": "form-select"}
            ),

            "banner": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def clean_banner(self):
        image = self.cleaned_data.get("banner")
        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Event banners must be 5 MB or smaller.")
        if image and image.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise forms.ValidationError("Only JPG, PNG, and WebP banners are supported.")
        return image


class EventFeedbackForm(forms.ModelForm):

    class Meta:
        model = EventFeedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "5 - Excellent"),
                    (4, "4 - Very good"),
                    (3, "3 - Good"),
                    (2, "2 - Needs improvement"),
                    (1, "1 - Poor"),
                ],
                attrs={"class": "form-select"},
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Share your experience",
                }
            ),
        }

from .models import EventMember


class EventMemberForm(forms.ModelForm):

    class Meta:
        model = EventMember

        fields = [
            "event",
            "member_name",
            "email",
            "phone",
        ]

        widgets = {

            "event": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),

            "member_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter member name"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter email"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter phone number"
                }
            ),
        }

