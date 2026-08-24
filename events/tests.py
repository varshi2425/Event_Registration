from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from django.urls import reverse

from .models import (
	Event,
	EventCategory,
	EventFeedback,
	EventMember,
	EventWishlist,
	mark_completed_events,
)


class UserQrCodeTests(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username="qr-user",
			password="test-password-123",
		)
		self.other_user = User.objects.create_user(
			username="other-user",
			password="test-password-123",
		)
		category = EventCategory.objects.create(
			category_name="Conference",
			category_code="CONF",
			priority=1,
		)
		self.event = Event.objects.create(
			event_name="User Conference",
			event_code="USER-CONF",
			category=category,
			description="A test conference",
			venue="Main Hall",
			start_date="2026-09-01",
			end_date="2026-09-01",
			max_participants=100,
		)
		EventMember.objects.create(
			user=self.user,
			event=self.event,
			member_name="QR User",
			email="qr@example.com",
			phone="1234567890",
		)
		EventMember.objects.create(
			user=self.other_user,
			event=self.event,
			member_name="Other User",
			email="other@example.com",
			phone="1234567891",
		)

	def test_user_sees_only_own_qr_registration(self):
		self.client.login(username="qr-user", password="test-password-123")

		response = self.client.get(reverse("my_qr_codes"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "QR User")
		self.assertNotContains(response, "Other User")

	def test_event_generates_registration_qr_code(self):
		self.assertTrue(self.event.event_qr_code)
		self.assertTrue(self.event.event_qr_code.name.startswith("event_qr_codes/"))

		response = self.client.get(
			reverse("event_details", kwargs={"id": self.event.id})
		)

		self.assertContains(response, self.event.event_qr_code.url)

	def test_user_events_repairs_missing_event_registration_qr_code(self):
		self.event.event_qr_code.delete(save=False)
		Event.objects.filter(id=self.event.id).update(event_qr_code=None)

		self.client.login(username="qr-user", password="test-password-123")
		response = self.client.get(reverse("user_events"))

		self.event.refresh_from_db()
		self.assertTrue(self.event.event_qr_code)
		self.assertContains(response, self.event.event_qr_code.url)

	def test_event_details_repairs_missing_event_qr_file(self):
		qr_name = self.event.event_qr_code.name
		self.event.event_qr_code.storage.delete(qr_name)

		response = self.client.get(
			reverse("event_details", kwargs={"id": self.event.id})
		)

		self.event.refresh_from_db()
		self.assertEqual(response.status_code, 200)
		self.assertTrue(self.event.event_qr_code.storage.exists(
			self.event.event_qr_code.name
		))
		self.assertContains(response, self.event.event_qr_code.url)

	def test_ended_event_is_marked_completed(self):
		self.event.end_date = timezone.localdate() - timedelta(days=1)
		self.event.status = "Ongoing"
		self.event.save()

		mark_completed_events()

		self.event.refresh_from_db()
		self.assertEqual(self.event.status, "Completed")

	def test_started_event_is_marked_ongoing(self):
		self.event.start_date = timezone.localdate()
		self.event.end_date = timezone.localdate() + timedelta(days=1)
		self.event.status = "Upcoming"
		self.event.save()

		mark_completed_events()

		self.event.refresh_from_db()
		self.assertEqual(self.event.status, "Ongoing")


class UserDashboardSearchTests(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username="search-user",
			password="test-password-123",
		)
		category = EventCategory.objects.create(
			category_name="Workshop",
			category_code="WORK",
			priority=1,
		)
		Event.objects.create(
			event_name="Python Session",
			event_code="PYTHON-01",
			category=category,
			description="Learn Python",
			venue="Training Room",
			start_date="2026-09-01",
			end_date="2026-09-01",
			max_participants=50,
		)
		self.client.login(
			username="search-user",
			password="test-password-123",
		)

	def test_search_matches_venue_and_category(self):
		venue_response = self.client.get(
			reverse("user_events"),
			{"search": "Training Room"},
		)
		category_response = self.client.get(
			reverse("user_events"),
			{"search": "Workshop"},
		)

		self.assertContains(venue_response, "Python Session")
		self.assertContains(category_response, "Python Session")


class RegistrationEnhancementTests(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username="registration-user",
			password="test-password-123",
		)
		self.staff = User.objects.create_user(
			username="staff-user",
			password="test-password-123",
			is_staff=True,
		)
		category = EventCategory.objects.create(
			category_name="Meetup",
			category_code="MEET",
			priority=1,
		)
		self.event = Event.objects.create(
			event_name="Django Meetup",
			event_code="DJANGO-01",
			category=category,
			description="A test meetup",
			venue="Auditorium",
			start_date="2026-09-01",
			end_date="2026-09-01",
			max_participants=50,
		)
		self.registration = EventMember.objects.create(
			user=self.user,
			event=self.event,
			member_name="Registration User",
			email="registration@example.com",
			phone="1234567890",
		)

	def test_user_can_cancel_own_registration(self):
		self.client.login(username="registration-user", password="test-password-123")

		response = self.client.post(
			reverse("cancel_registration", kwargs={"id": self.registration.id})
		)

		self.assertRedirects(response, reverse("my_registrations"))
		self.assertFalse(EventMember.objects.filter(id=self.registration.id).exists())

	def test_user_can_add_and_remove_event_from_wishlist(self):
		self.client.login(username="registration-user", password="test-password-123")
		wishlist_url = reverse(
			"toggle_wishlist",
			kwargs={"id": self.event.id},
		)

		add_response = self.client.post(wishlist_url)

		self.assertRedirects(
			add_response,
			reverse("event_details", kwargs={"id": self.event.id}),
		)
		self.assertTrue(
			EventWishlist.objects.filter(
				user=self.user,
				event=self.event,
			).exists()
		)

		remove_response = self.client.post(wishlist_url)

		self.assertRedirects(
			remove_response,
			reverse("event_details", kwargs={"id": self.event.id}),
		)
		self.assertFalse(
			EventWishlist.objects.filter(
				user=self.user,
				event=self.event,
			).exists()
		)

	def test_wishlist_page_shows_only_current_users_events(self):
		EventWishlist.objects.create(user=self.user, event=self.event)
		self.client.login(username="registration-user", password="test-password-123")

		response = self.client.get(reverse("wishlist"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Django Meetup")

	def test_staff_cannot_use_user_wishlist(self):
		self.client.login(username="staff-user", password="test-password-123")

		response = self.client.get(reverse("wishlist"))

		self.assertRedirects(response, reverse("admin_dashboard"))

	def test_staff_check_in_marks_member_once(self):
		self.client.login(username="staff-user", password="test-password-123")
		check_in_url = reverse(
			"check_in",
			kwargs={
				"event_id": self.event.id,
				"qr_token": self.registration.qr_token,
			},
		)

		first_response = self.client.get(check_in_url)
		self.registration.refresh_from_db()
		first_checked_in_at = self.registration.checked_in_at

		self.assertEqual(first_response.status_code, 200)
		self.assertContains(first_response, "Check-In Successful")
		self.assertTrue(self.registration.is_checked_in)
		self.assertIsNotNone(first_checked_in_at)

		second_response = self.client.get(check_in_url)
		self.registration.refresh_from_db()

		self.assertEqual(second_response.status_code, 200)
		self.assertContains(second_response, "Already Checked In")
		self.assertEqual(self.registration.checked_in_at, first_checked_in_at)

	def test_check_in_rejects_qr_from_another_event(self):
		other_event = Event.objects.create(
			event_name="Other Meetup",
			event_code="OTHER-01",
			category=self.event.category,
			description="Another test event",
			venue="Other Hall",
			start_date="2026-09-02",
			end_date="2026-09-02",
			max_participants=50,
		)
		self.client.login(username="staff-user", password="test-password-123")
		check_in_url = reverse(
			"check_in",
			kwargs={
				"event_id": other_event.id,
				"qr_token": self.registration.qr_token,
			},
		)

		response = self.client.get(check_in_url)

		self.assertRedirects(response, reverse("qr_scanner", kwargs={"event_id": other_event.id}))
		self.registration.refresh_from_db()
		self.assertFalse(self.registration.is_checked_in)

	@patch("events.views.send_mail")
	def test_registration_sends_confirmation_email(self, send_mail_mock):
		self.registration.delete()
		self.client.login(username="registration-user", password="test-password-123")

		response = self.client.post(
			reverse("register_event", kwargs={"id": self.event.id}),
			{
				"member_name": "New Attendee",
				"email": "attendee@example.com",
				"phone": "9876543210",
			},
		)

		self.assertRedirects(response, reverse("user_dashboard"))
		send_mail_mock.assert_called_once()
		self.assertEqual(
			send_mail_mock.call_args.kwargs["recipient_list"],
			["attendee@example.com"],
		)
		self.assertIn(
			"Registration confirmed: Django Meetup",
			send_mail_mock.call_args.kwargs["subject"],
		)

	def test_staff_can_export_attendance_csv(self):
		self.client.login(username="staff-user", password="test-password-123")

		response = self.client.get(reverse("export_attendance"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response["Content-Type"], "text/csv")
		self.assertIn("Django Meetup", response.content.decode())

	def test_staff_can_view_feedback_and_regular_users_cannot(self):
		EventFeedback.objects.create(
			event=self.event,
			user=self.user,
			rating=5,
			comment="Excellent event",
		)

		self.client.login(username="staff-user", password="test-password-123")
		staff_response = self.client.get(reverse("feedback_list"))
		self.assertEqual(staff_response.status_code, 200)
		self.assertContains(staff_response, "Excellent event")

		self.client.logout()
		self.client.login(username="registration-user", password="test-password-123")
		user_response = self.client.get(reverse("feedback_list"))
		self.assertRedirects(user_response, reverse("user_dashboard"))

	def test_user_can_save_and_update_feedback(self):
		self.client.login(username="registration-user", password="test-password-123")
		feedback_url = reverse(
			"submit_feedback",
			kwargs={"id": self.event.id},
		)

		response = self.client.post(
			feedback_url,
			{"rating": "5", "comment": "Excellent event"},
		)
		self.assertRedirects(response, reverse("event_details", kwargs={"id": self.event.id}))
		self.assertEqual(EventFeedback.objects.filter(event=self.event, user=self.user).count(), 1)

		self.client.post(
			feedback_url,
			{"rating": "4", "comment": "Updated comment"},
		)
		feedback = EventFeedback.objects.get(event=self.event, user=self.user)
		self.assertEqual(feedback.rating, 4)
		self.assertEqual(feedback.comment, "Updated comment")

# Create your tests here.
