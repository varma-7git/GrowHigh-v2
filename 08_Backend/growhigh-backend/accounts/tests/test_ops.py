from django.test import TestCase
from rest_framework.test import APIClient


class HealthTests(TestCase):
    def test_health_is_public_and_reports_database(self):
        r = APIClient().get("/api/v1/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok", "database": "ok"})


class LoginLoggingTests(TestCase):
    def test_failed_login_is_logged_without_the_password(self):
        with self.assertLogs("growhigh.auth", level="WARNING") as cm:
            r = APIClient().post("/api/v1/auth/login/", {"login_id": "nobody@example.com", "password": "Secret123"}, format="json")
        self.assertEqual(r.status_code, 401)
        text = "\n".join(cm.output)
        self.assertIn("nobody@example.com", text)
        self.assertNotIn("Secret123", text)
