from django.urls import path
from . import views

urlpatterns = [

    path(
        "create-category/",
        views.create_category,
        name="create_category"
    ),
    path(
    "category-list/",
    views.category_list,
    name="category_list",
),

path(
    "edit-category/<int:id>/",
    views.edit_category,
    name="edit_category"
),

path(
    "delete-category/<int:id>/",
    views.delete_category,
    name="delete_category"
),

path(
    "create-event/",
    views.create_event,
    name="create_event"
),
path(
    "event-list/",
    views.event_list,
    name="event_list"
),
path(
    "feedback/",
    views.feedback_list,
    name="feedback_list"
),
path(
    "edit-event/<int:id>/",
    views.edit_event,
    name="edit_event"
),
path(
    "delete-event/<int:id>/",
    views.delete_event,
    name="delete_event"
),
path(
    "event-details/<int:id>/",
    views.event_details,
    name="event_details"
),
path(
    "event-details/<int:id>/feedback/",
    views.submit_feedback,
    name="submit_feedback"
),
path(
    "add-member/",
    views.add_event_member,
    name="add_event_member"
),
path(
    "member-list/",
    views.member_list,
    name="member_list"
),
path(
    "edit-member/<int:id>/",
    views.edit_member,
    name="edit_member"
),
path(
    "delete-member/<int:id>/",
    views.delete_member,
    name="delete_member"
),
path(
    "check-in/<int:event_id>/<uuid:qr_token>/",
    views.check_in,
    name="check_in",
),

path(
    "qr-scanner/<int:event_id>/",
    views.qr_scanner,
    name="qr_scanner"
),

path(
    "qr-scanner/",
    views.qr_scanner_home,
    name="qr_scanner_home"
),

path(
    "register-event/<int:id>/",
    views.register_event,
    name="register_event"
),

path(
    "cancel-registration/<int:id>/",
    views.cancel_registration,
    name="cancel_registration"
),

path(
    "export-attendance/",
    views.export_attendance,
    name="export_attendance"
),

path(
    "my-qr-codes/",
    views.my_qr_codes,
    name="my_qr_codes"
),


]