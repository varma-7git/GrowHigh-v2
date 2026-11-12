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


class AdminPasswordFieldTests(TestCase):
    def test_password_is_not_an_editable_box_in_django_admin(self):
        from accounts.models import User
        boss = User.objects.create_superuser("boss", "Boss12345")
        faculty = User.objects.create_user("CM-777", "Faculty123", role="FACULTY", full_name="F", email="f@example.com")
        self.client.force_login(boss)
        r = self.client.get(f"/admin/accounts/user/{faculty.id}/change/")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'name="password"')


class ResetCodeTests(TestCase):
    def test_five_wrong_tries_lock_the_code_and_a_new_code_unlocks(self):
        import re
        from django.core import mail
        from accounts.models import User
        User.objects.create_user("S1", "Start@1234", full_name="S One", email="s1@example.com")
        c = APIClient()
        c.post("/api/v1/auth/forgot-password/", {"login_id": "S1"}, format="json")
        code = re.search(r"\n\n(\d{6})\n\n", mail.outbox[0].body).group(1)
        wrong = "000000" if code != "000000" else "111111"
        url = "/api/v1/auth/verify-reset-code/"
        for _ in range(5):
            self.assertEqual(c.post(url, {"login_id": "S1", "code": wrong}, format="json").status_code, 400)
        self.assertEqual(c.post(url, {"login_id": "S1", "code": code}, format="json").status_code, 400)  # locked
        mail.outbox.clear()
        c.post("/api/v1/auth/forgot-password/", {"login_id": "S1"}, format="json")  # a new code unlocks
        fresh = re.search(r"\n\n(\d{6})\n\n", mail.outbox[0].body).group(1)
        r = c.post(url, {"login_id": "S1", "code": fresh}, format="json")
        self.assertEqual(r.status_code, 200)
        weak = c.post("/api/v1/auth/reset-password/", {"token": r.data["token"], "new_password": "short", "confirm_password": "short"}, format="json")
        self.assertEqual(weak.status_code, 400)  # a rejected password does not use up the proof
        ok = c.post("/api/v1/auth/reset-password/", {"token": r.data["token"], "new_password": "NewPass@123", "confirm_password": "NewPass@123"}, format="json")
        self.assertEqual(ok.status_code, 204)


class FirstLoginTests(TestCase):
    def test_login_says_first_login_only_once(self):
        from accounts.models import User
        User.objects.create_user("F1", "Start@1234", full_name="F One", email="f1@example.com")
        c = APIClient()
        first = c.post("/api/v1/auth/login/", {"login_id": "F1", "password": "Start@1234"}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data["first_login"])
        again = c.post("/api/v1/auth/login/", {"login_id": "F1", "password": "Start@1234"}, format="json")
        self.assertFalse(again.data["first_login"])
