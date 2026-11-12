"""Creates a ready-to-take demo test for the CSE branch (year 2) and a demo student.

    py manage.py seed_demo

It uses the same API the app uses, so it exercises the real rules. Safe to run again: the student is reused,
and a new test is added each time.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from rest_framework.test import APIClient

from academics.models import Branch, Topic
from accounts.models import StudentProfile, User
from common.constants import Role

STUDENT_ID, STUDENT_PASSWORD = "DEMO-STU", "Demo@1234"
FACULTY_ID, FACULTY_PASSWORD = "DEMO-FAC", "Demo@1234"

QUESTIONS = [
    ("Which data structure works on First In First Out?", ["Stack", "Queue", "Tree", "Graph"], 1, "A queue removes the oldest item first."),
    ("Which keyword defines a function in Python?", ["func", "define", "def", "lambda only"], 2, "Python uses def."),
    ("What is the binary form of decimal 5?", ["100", "101", "110", "111"], 1, "5 = 4 + 1 = 101."),
    ("Which of these is not a programming language?", ["Python", "Java", "HTML", "C"], 2, "HTML is a markup language."),
    ("What does CPU stand for?", ["Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Control Process Unit"], 0, "CPU = Central Processing Unit."),
]


def find_topic(branch):
    """First topic that belongs to this branch; falls back to any topic, with a warning from the caller."""
    for lookup in ("subject__branch", "subject__semester__branch"):
        try:
            t = Topic.objects.filter(**{lookup: branch}).order_by("id").first()
        except Exception:
            continue
        if t:
            return t, True
    return Topic.objects.order_by("id").first(), False


class Command(BaseCommand):
    help = "Create a demo test for CSE year 2 and a demo student to take it."

    def handle(self, *args, **opts):
        branch = Branch.objects.filter(code__iexact="CSE").first() or Branch.objects.filter(name__icontains="computer science").first()
        if not branch:
            raise CommandError("No CSE branch found. Run import_curriculum first.")
        topic, matched = find_topic(branch)
        if not topic:
            raise CommandError("No topics found. Run import_curriculum first.")

        fac = User.objects.filter(login_id=FACULTY_ID).first()
        if not fac:
            fac = User.objects.create_user(login_id=FACULTY_ID, password=FACULTY_PASSWORD, full_name="Demo Faculty", role=Role.FACULTY)
        stu = User.objects.filter(login_id=STUDENT_ID).first()
        if not stu:
            stu = User.objects.create_user(login_id=STUDENT_ID, password=STUDENT_PASSWORD, full_name="Demo Student", role=Role.STUDENT)
            StudentProfile.objects.create(user=stu, branch=branch, year_of_study=2)

        api = APIClient(HTTP_HOST="localhost")
        api.force_authenticate(fac)
        ids = []
        for text, options, correct, why in QUESTIONS:
            r = api.post("/api/v1/questions/", {"topic_id": topic.pk, "text": text, "options": options, "correct": correct, "explanation": why}, format="json")
            if r.status_code not in (200, 201):
                raise CommandError(f"Could not add a question: {r.status_code} {getattr(r, 'data', '')}")
            ids.append(r.data["id"])

        start = timezone.localtime() - timedelta(minutes=1)
        r = api.post("/api/v1/tests/", {"name": "Demo CSE test", "test_type": "DAILY", "scheduled_date": str(start.date()),
                                        "start_time": start.strftime("%H:%M:%S"), "duration_minutes": 60,
                                        "branch_id": branch.pk, "year_of_study": 2, "question_ids": ids}, format="json")
        if r.status_code not in (200, 201):
            raise CommandError(f"Could not create the test: {r.status_code} {getattr(r, 'data', '')}")
        tid = r.data["id"]
        r = api.post(f"/api/v1/tests/{tid}/assign/", {"student_ids": [stu.pk]}, format="json")
        if r.status_code not in (200, 201):
            raise CommandError(f"Could not assign the test: {r.status_code} {getattr(r, 'data', '')}")

        if not matched:
            self.stdout.write(self.style.WARNING(f"Note: no topic linked to {branch.code} was found, so questions went into '{topic.name}'."))
        self.stdout.write(self.style.SUCCESS(
            f"Done. Test #{tid} 'Demo CSE test' ({len(ids)} questions, 60 minutes, open now) for {branch.code} year 2.\n"
            f"Student login: {STUDENT_ID} / {STUDENT_PASSWORD}\nFaculty login (to see results): {FACULTY_ID} / {FACULTY_PASSWORD}"))
