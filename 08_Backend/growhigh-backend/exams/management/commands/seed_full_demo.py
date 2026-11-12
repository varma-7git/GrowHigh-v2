"""Fills GrowHigh with sample data by acting as admin, faculty and students through the real API.

    py manage.py seed_full_demo

Admin   : (demo admin DEMO-ADM) branch, subject, topics, previous-year paper, jobs and internships, Job preparation / Career growth / Communication lessons
Faculty : learning material, questions, daily + weekly tests, assigns the tests
Students: three demo students take the tests and a practice set, then the results are printed.

Everything is named "Demo ..." so it is easy to spot. Run it once on a development database.
"""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from rest_framework.test import APIClient

from academics.models import Branch
from accounts.models import StudentProfile, User
from common.constants import Role
from exams.models import Question

PASSWORD = "Demo@1234"
STUDENTS = [("DEMO-STU", "Demo Student One", 0.9), ("DEMO-STU2", "Demo Student Two", 0.6), ("DEMO-STU3", "Demo Student Three", 0.3)]

TOPICS = {
    "Python basics": [
        ("Which keyword defines a function in Python?", ["func", "define", "def", "lambda only"], 2, "Python uses def."),
        ("What is the output type of 3 / 2 in Python 3?", ["int", "float", "str", "bool"], 1, "The / operator always gives a float."),
        ("Which symbol starts a comment in Python?", ["//", "#", "/*", "--"], 1, "# starts a comment."),
        ("Which of these is a mutable type?", ["tuple", "str", "list", "int"], 2, "Lists can be changed in place."),
    ],
    "Data structures": [
        ("Which data structure works on First In First Out?", ["Stack", "Queue", "Tree", "Graph"], 1, "A queue removes the oldest item first."),
        ("Which structure works on Last In First Out?", ["Queue", "Array", "Stack", "Heap"], 2, "A stack removes the newest item first."),
        ("Searching a sorted array by halving is called?", ["Linear search", "Binary search", "Hashing", "Sorting"], 1, "Binary search halves the range each time."),
        ("A node with no children in a tree is a?", ["Root", "Leaf", "Branch", "Parent"], 1, "Leaf nodes have no children."),
    ],
    "Database basics": [
        ("Which SQL command reads rows from a table?", ["INSERT", "UPDATE", "SELECT", "DELETE"], 2, "SELECT reads data."),
        ("A key that uniquely identifies a row is the?", ["Foreign key", "Primary key", "Index", "View"], 1, "The primary key is unique per row."),
        ("Which command removes a table completely?", ["DELETE", "DROP", "REMOVE", "CLEAR"], 1, "DROP TABLE removes it."),
        ("What does SQL stand for?", ["Structured Query Language", "Simple Query Logic", "Stored Query List", "System Query Layer"], 0, "SQL = Structured Query Language."),
    ],
}

PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
       b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF")


class Command(BaseCommand):
    help = "Fill the app with sample data as admin, faculty and students, then print the results."

    # ---------- helpers
    def api(self, user):
        c = APIClient(HTTP_HOST="localhost")
        c.force_authenticate(user)
        return c

    def ok(self, r, what):
        if r.status_code not in (200, 201, 204):
            raise CommandError(f"{what} failed: {r.status_code} {getattr(r, 'data', '')}")
        return r.data if r.status_code != 204 else None

    def say(self, text):
        self.stdout.write(text)

    def step(self, text):
        self.stdout.write(self.style.MIGRATE_HEADING(text))

    # ---------- main
    def handle(self, *args, **opts):
        admin_user = User.objects.filter(login_id="DEMO-ADM").first() or User.objects.create_user(
            login_id="DEMO-ADM", password=PASSWORD, full_name="Demo Admin", role=Role.ADMIN)
        cse = Branch.objects.filter(code__iexact="CSE").first()
        if not cse:
            raise CommandError("No CSE branch found. Run import_curriculum first.")

        faculty = User.objects.filter(login_id="DEMO-FAC").first() or User.objects.create_user(
            login_id="DEMO-FAC", password=PASSWORD, full_name="Demo Faculty", role=Role.FACULTY)
        students = []
        for login, name, skill in STUDENTS:
            u = User.objects.filter(login_id=login).first()
            if not u:
                u = User.objects.create_user(login_id=login, password=PASSWORD, full_name=name, role=Role.STUDENT)
                StudentProfile.objects.create(user=u, branch=cse, year_of_study=2)
            students.append((u, skill))

        A, F = self.api(admin_user), self.api(faculty)

        # ---------- ADMIN
        self.step("Admin: branch, regulation, subject, topics")
        regs = self.ok(A.get("/api/v1/regulations/"), "list regulations")
        regs = regs["results"] if isinstance(regs, dict) else regs
        c23 = next((r for r in regs if r["code"] == "C23"), None) or self.ok(A.post("/api/v1/regulations/", {"code": "C23", "name": "C23"}, format="json"), "add regulation")
        if not Branch.objects.filter(code="DEMO").exists():
            self.ok(A.post("/api/v1/branches/", {"name": "Demo Branch", "code": "DEMO"}, format="json"), "add branch")
            self.say("  branch: Demo Branch (DEMO)")
        subject = self.ok(A.post("/api/v1/subjects/", {"area": "ECET", "name": "Demo Programming and Databases", "code": "DEMO-301", "marks": 50,
                                                      "branch_id": cse.pk, "regulation_id": c23["id"], "semester": 3, "is_active": True}, format="json"), "add subject")
        topics = {}
        for i, name in enumerate(TOPICS):
            topics[name] = self.ok(A.post("/api/v1/topics/", {"subject_id": subject["id"], "name": name, "description": f"Demo topic: {name}", "order_no": i}, format="json"), "add topic")
        self.say(f"  subject: {subject['name']} with {len(topics)} topics")

        self.step("Admin: previous year paper")
        self.ok(A.post("/api/v1/papers/", {"year": 2023, "title": "Demo previous year paper", "branch_id": cse.pk,
                                           "file": SimpleUploadedFile("demo_paper.pdf", PDF, content_type="application/pdf")}, format="multipart"), "upload paper")
        self.say("  paper: 2023 Demo previous year paper")

        self.step("Admin: jobs and internships")
        deadline = str(timezone.localdate() + timedelta(days=30))
        for title, company, kind, loc, dur, pay in [
            ("Demo Junior Python Developer", "Demo Tech Pvt Ltd", "JOB", "Hyderabad", "", "3 LPA"),
            ("Demo Web Support Engineer", "Demo Systems", "JOB", "Vijayawada", "", "2.4 LPA"),
            ("Demo Web Development Intern", "Demo Tech Pvt Ltd", "INTERNSHIP", "Remote", "3 months", "5000 per month"),
            ("Demo Data Entry Intern", "Demo Systems", "INTERNSHIP", "Visakhapatnam", "2 months", "Unpaid"),
        ]:
            self.ok(A.post("/api/v1/jobs/", {"title": title, "company_name": company, "job_type": kind, "location": loc, "duration": dur, "pay": pay,
                                             "deadline": deadline, "description": f"{title} at {company}. Sample listing for testing.", "branch_ids": []}, format="json"), "add job")
        self.say("  2 jobs and 2 internships")

        self.step("Admin: Job preparation, Career growth and Communication lessons")
        lessons = [
            ("JOB_PREP", "aptitude", "Percentages made easy", "Percent means per hundred. 25% of 80 = 80 x 25 / 100 = 20."),
            ("JOB_PREP", "coding", "Reverse a string", "In Python: s[::-1]. Practise writing it with a loop too."),
            ("JOB_PREP", "hr", "Tell me about yourself", "Answer in three parts: who you are, what you studied and built, what you want next."),
            ("CAREER", "technologies", "Technologies to learn first", "Start with Python, SQL and Git, then add one web framework."),
            ("CAREER", "roadmap", "Stage 1: Fundamentals", "Programming basics, data structures and a small project."),
            ("COMM", "spoken", "Introduce yourself", "Say your name, college, branch and one goal in simple sentences."),
            ("COMM", "grammar", "Present tense", "I study, you study, he studies. Add s or es for he, she and it."),
        ]
        for i, (area, section, title, body) in enumerate(lessons):
            self.ok(A.post("/api/v1/guides/", {"area": area, "section": section, "kind": "NOTES", "title": f"Demo: {title}", "body": body, "order_no": i}, format="json"), "add lesson")
        self.say(f"  {len(lessons)} lessons")

        # ---------- FACULTY
        self.step("Faculty: study material and questions")
        qids = {}
        for tname, qs in TOPICS.items():
            t = topics[tname]
            self.ok(F.post("/api/v1/materials/", {"topic_id": t["id"], "kind": "NOTES", "title": f"Demo notes: {tname}",
                                                  "body": f"Short revision notes for {tname}. Read these before the practice test."}, format="json"), "add material")
            qids[tname] = []
            for text, options, correct, why in qs:
                d = self.ok(F.post("/api/v1/questions/", {"topic_id": t["id"], "text": text, "options": options, "correct": correct, "explanation": why}, format="json"), "add question")
                qids[tname].append(d["id"])
        all_q = [q for ids in qids.values() for q in ids]
        self.say(f"  {len(topics)} materials, {len(all_q)} questions")

        self.step("Faculty: create and assign tests")
        start = timezone.localtime() - timedelta(minutes=1)
        test_ids = []
        for name, ttype, ids in [("Demo daily test", "DAILY", all_q[:6]), ("Demo weekly test", "WEEKLY", all_q)]:
            t = self.ok(F.post("/api/v1/tests/", {"name": name, "test_type": ttype, "scheduled_date": str(start.date()), "start_time": start.strftime("%H:%M:%S"),
                                                  "duration_minutes": 120, "branch_id": cse.pk, "year_of_study": 2, "question_ids": ids}, format="json"), f"create {name}")
            self.ok(F.post(f"/api/v1/tests/{t['id']}/assign/", {"student_ids": [u.pk for u, _ in students]}, format="json"), f"assign {name}")
            test_ids.append((t["id"], name))
        self.say(f"  {len(test_ids)} tests assigned to {len(students)} students")

        # ---------- STUDENTS
        self.step("Students: take the tests and a practice set")
        results = []
        for u, skill in students:
            S = self.api(u)
            for tid, name in test_ids:
                run = self.ok(S.post(f"/api/v1/tests/{tid}/start/"), f"{u.login_id} start {name}")
                res = self.submit(S, run, skill)
                results.append((u.full_name, name, res))
            practice = self.ok(S.post("/api/v1/practice/start/", {"kind": "topic", "topic_id": topics["Python basics"]["id"], "count": 4}, format="json"), "start practice")
            results.append((u.full_name, "Practice: Python basics", self.submit(S, practice, skill)))

        self.step("Results")
        for who, what, r in results:
            self.say(f"  {who:<22} {what:<26} {r['score']}/{r['total']}  {r['percent']}%  {'PASS' if r['passed'] else 'FAIL'}")
        self.step("Faculty performance summary (from the API)")
        for path in ("/api/v1/performance/summary/", "/api/v1/performance/students/"):
            r = F.get(path)
            self.say(f"  GET {path} -> {r.status_code}")
            if r.status_code == 200:
                self.say("    " + str(r.data)[:600])
        self.say(self.style.SUCCESS(
            f"\nDone. Log in as: admin DEMO-ADM, faculty DEMO-FAC, students DEMO-STU / DEMO-STU2 / DEMO-STU3 - password {PASSWORD}"))

    def submit(self, S, run, skill):
        """A student answers: roughly `skill` of the questions right, the rest wrong."""
        answers, n = {}, len(run["questions"])
        right = round(n * skill)
        for i, q in enumerate(run["questions"]):
            correct = Question.objects.get(pk=q["id"]).correct
            answers[q["id"]] = correct if i < right else (correct + 1) % 4
        return self.ok(S.post(f"/api/v1/attempts/{run['id']}/submit/", {"answers": answers}, format="json"), "submit attempt")
