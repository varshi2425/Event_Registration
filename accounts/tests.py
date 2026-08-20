from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Customization, Notification, Profile


class ChatbotTests(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username="chatbot-user",
			password="test-password-123",
		)
		self.client.login(
			username="chatbot-user",
			password="test-password-123",
		)

	def test_chatbot_returns_registration_guidance(self):
		response = self.client.post(
			reverse("chatbot_reply"),
			{"message": "How do I register?"},
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("Register", response.json()["reply"])

	def test_chatbot_requires_login(self):
		self.client.logout()

		response = self.client.post(
			reverse("chatbot_reply"),
			{"message": "Hello"},
		)

		self.assertEqual(response.status_code, 302)


class ProfilePictureTests(TestCase):

	def test_default_profile_picture_is_rendered(self):
		user = User.objects.create_user(
			username="profile-user",
			password="test-password-123",
		)
		self.client.login(
			username="profile-user",
			password="test-password-123",
		)

		Profile.objects.get(user=user)
		response = self.client.get(reverse("profile"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "profile_pictures/default.jpeg")


class UserDashboardFeatureTests(TestCase):

	def setUp(self):
		self.user = User.objects.create_user(
			username="dashboard-user",
			password="test-password-123",
		)
		self.client.login(
			username="dashboard-user",
			password="test-password-123",
		)

	def test_dashboard_renders_calendar_notifications_and_customization(self):
		Notification.objects.create(
			title="Event update",
			message="An event was updated.",
		)

		response = self.client.get(reverse("user_dashboard"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Dashboard Customization")
		self.assertContains(response, "Event update")
		self.assertContains(response, reverse("user_calendar"))
		self.assertContains(response, "View All Notifications")

	def test_user_calendar_and_notifications_are_separate_pages(self):
		calendar_response = self.client.get(reverse("user_calendar"))
		notification_response = self.client.get(reverse("notification_list"))

		self.assertEqual(calendar_response.status_code, 200)
		self.assertContains(calendar_response, "Monthly Calendar")
		self.assertContains(calendar_response, "userCalendar")
		self.assertEqual(notification_response.status_code, 200)
		self.assertContains(notification_response, "All Notifications")

	def test_user_can_save_dashboard_customization(self):
		response = self.client.post(
			reverse("user_dashboard"),
			{
				"dashboard_title": "My Events",
				"theme": "dark",
				"sidebar_color": "#123456",
				"topbar_color": "#ffffff",
				"font_size": "large",
			},
		)

		self.assertRedirects(response, reverse("user_dashboard"))
		customization = Customization.objects.get(user=self.user)
		self.assertEqual(customization.dashboard_title, "My Events")
		self.assertEqual(customization.theme, "dark")

	def test_password_reset_page_is_available(self):
		response = self.client.get(reverse("password_reset"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Reset your password")
