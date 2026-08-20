from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Event, EventCategory, EventFeedback, EventMember


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
