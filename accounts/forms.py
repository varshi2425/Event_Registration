from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Profile, SupportRequest, Customization


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email"
        ]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "profile_picture",
            "phone",
            "address"
        ]

    def clean_profile_picture(self):
        image = self.cleaned_data.get("profile_picture")
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError("Profile pictures must be 5 MB or smaller.")
        if image and image.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        }:
            raise ValidationError("Only JPG, PNG, and WebP images are supported.")
        return image


class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = [
            "name",
            "email",
            "phone",
            "subject",
            "message"
        ]



from django import forms
from .models import Customization


class CustomizationForm(forms.ModelForm):

    class Meta:
        model = Customization

        fields = [
            "dashboard_title",
            "theme",
            "sidebar_color",
            "topbar_color",
            "font_size",
        ]

        widgets = {

            "dashboard_title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter dashboard title"
            }),

            "theme": forms.Select(attrs={
                "class": "form-select"
            }),

            "sidebar_color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "style": "height:55px;"
            }),

            "topbar_color": forms.TextInput(attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "style": "height:55px;"
            }),

            "font_size": forms.Select(attrs={
                "class": "form-select"
            }),

        }