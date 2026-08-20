from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [

    path('', views.login_view, name='login'),

    path('signup/', views.signup_view, name='signup'),

    path('logout/', views.logout_view, name='logout'),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/password-reset/complete/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'user-dashboard/',
        views.user_dashboard,
        name='user_dashboard'
    ),

    path(
        "user-events/",
        views.user_events,
        name="user_events"
    ),

    path(
        "user-calendar/",
        views.user_calendar,
        name="user_calendar"
    ),

    path(
        "my-registrations/",
        views.my_registrations,
        name="my_registrations"
    ),

    path(
        "profile/",
        views.profile,
        name="profile"
    ),

    path(
        "edit-profile/",
        views.edit_profile,
        name="edit_profile"
    ),

    path(
        "change-password/",
        views.change_password,
        name="change_password"
    ),

    path(
        "contact-support/",
        views.contact_support,
        name="contact_support"
    ),

    path(
        "chatbot/reply/",
        views.chatbot_reply,
        name="chatbot_reply"
    ),

    path(
        'update-support-status/<int:id>/',
        views.update_support_status,
        name='update_support_status'
    ),

    path(
        "notifications/read/",
        views.mark_notifications_read,
        name="mark_notifications_read"
    ),

    path(
        "notifications/",
        views.notification_list,
        name="notification_list"
),
    path(
    "reset-customization/",
    views.reset_customization,
    name="reset_customization",
),
    
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )