from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Branch, Guide, GuideDone
from academics.tracking import GuideQuestion
from accounts.models import StudentProfile, User
from common.constants import Role

API = "/api/v1"


class TrackingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("TADM", "Start@1234", full_name="Admin", role=Role.ADMIN)
        self.stu = User.objects.create_user("TSTU", "Start@1234", full_name="Stu", role=Role.STUDENT)
        StudentProfile.objects.create(user=self.stu, branch=Branch.objects.create(name="Test", code="TST"), year_of_study=1)
        self.guide = Guide.objects.create(area="JOB_PREP", section="aptitude", kind="NOTES", title="Percentages", body="x")

    def as_user(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_quiz_pass_completes_lesson_and_fail_does_not(self):
        a = self.as_user(self.admin)
        for i in range(2):
            r = a.post(f"{API}/guide-questions/", {"guide_id": self.guide.pk, "text": f"Q{i}", "options": ["a", "b", "c", "d"], "correct": 1}, format="json")
            self.assertEqual(r.status_code, 201, r.data)
        s = self.as_user(self.stu)
        qs = s.get(f"{API}/guides/{self.guide.pk}/quiz/").data["questions"]
        self.assertEqual(len(qs), 2)
        self.assertNotIn("correct", qs[0])
        bad = s.post(f"{API}/guides/{self.guide.pk}/quiz/", {"answers": {str(q["id"]): 0 for q in qs}}, format="json")
        self.assertEqual(bad.data["percent"], 0)
        self.assertFalse(GuideDone.objects.filter(user=self.stu, guide=self.guide).exists())
        good = s.post(f"{API}/guides/{self.guide.pk}/quiz/", {"answers": {str(q["id"]): 1 for q in qs}}, format="json")
        self.assertTrue(good.data["passed"])
        self.assertFalse(good.data["lesson_completed"])  # the hands-on task is still to do
        self.assertFalse(GuideDone.objects.filter(user=self.stu, guide=self.guide).exists())
        done = s.post(f"{API}/guides/{self.guide.pk}/submit/", {"text": "Percent means per hundred, so 25% of 80 is 20."}, format="multipart")
        self.assertTrue(done.data["lesson_completed"])
        self.assertTrue(GuideDone.objects.filter(user=self.stu, guide=self.guide).exists())

    def test_recording_completes_speaking_prompt(self):
        g = Guide.objects.create(area="COMM", section="speaking", kind="NOTES", title="Introduce yourself", body="x")
        r = self.as_user(self.stu).post(f"{API}/recordings/", {"guide_id": g.pk, "seconds": 5,
                                       "file": SimpleUploadedFile("a.webm", b"\x1aE\xdf\xa3audio", content_type="audio/webm")}, format="multipart")
        self.assertEqual(r.status_code, 201, getattr(r, "data", None))
        self.assertTrue(GuideDone.objects.filter(user=self.stu, guide=g).exists())

    def test_career_goals_are_private_to_the_student(self):
        s = self.as_user(self.stu)
        r = s.post(f"{API}/career-goals/", {"title": "Learn SQL", "target_date": "2026-12-31", "notes": "Start with SELECT"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        other = User.objects.create_user("TSTU2", "Start@1234", full_name="Other", role=Role.STUDENT)
        seen = self.as_user(other).get(f"{API}/career-goals/").data
        self.assertEqual(len(seen["results"] if isinstance(seen, dict) else seen), 0)
        done = s.patch(f"{API}/career-goals/{r.data['id']}/", {"status": "DONE"}, format="json")
        self.assertEqual(done.data["status"], "DONE")


class TaskTests(TrackingTests):
    def test_written_task_completes_and_faculty_can_review(self):
        s = self.as_user(self.stu)
        tasks = s.get(f"{API}/guide-tasks/?area=JOB_PREP&section=aptitude").data
        self.assertEqual(tasks[str(self.guide.pk)]["type"], "WRITTEN")
        short = s.post(f"{API}/guides/{self.guide.pk}/submit/", {"text": "too short"}, format="multipart")
        self.assertEqual(short.status_code, 400)
        self.assertFalse(GuideDone.objects.filter(user=self.stu, guide=self.guide).exists())
        ok = s.post(f"{API}/guides/{self.guide.pk}/submit/", {"text": "Percent means per hundred, so 25% of 80 is 20."}, format="multipart")
        self.assertEqual(ok.status_code, 201, getattr(ok, "data", None))
        self.assertTrue(GuideDone.objects.filter(user=self.stu, guide=self.guide).exists())
        fac = User.objects.create_user("TFAC", "Start@1234", full_name="Fac", role=Role.FACULTY)
        f = self.as_user(fac)
        rows = f.get(f"{API}/guide-submissions/?pending=1").data
        rows = rows["results"] if isinstance(rows, dict) else rows
        self.assertEqual(len(rows), 1)
        r = f.patch(f"{API}/guide-submissions/{rows[0]['id']}/", {"feedback": "Good start."}, format="json")
        self.assertEqual(r.status_code, 200, getattr(r, "data", None))
        self.assertEqual(r.data["reviewed_by_name"], "Fac")

    def test_admin_can_make_a_lesson_an_upload_task(self):
        a = self.as_user(self.admin)
        self.assertEqual(a.put(f"{API}/guides/{self.guide.pk}/task-setting/", {"task_type": "UPLOAD", "prompt": "Upload your project."}, format="json").status_code, 200)
        s = self.as_user(self.stu)
        self.assertEqual(s.get(f"{API}/guide-tasks/").data[str(self.guide.pk)]["type"], "UPLOAD")
        no_file = s.post(f"{API}/guides/{self.guide.pk}/submit/", {"text": "x"}, format="multipart")
        self.assertEqual(no_file.status_code, 400)
        f = SimpleUploadedFile("project.pdf", b"%PDF-1.4 demo", content_type="application/pdf")
        self.assertEqual(s.post(f"{API}/guides/{self.guide.pk}/submit/", {"file": f}, format="multipart").status_code, 201)


class TaskTypeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("TADM2", "Start@1234", full_name="Admin", role=Role.ADMIN)
        self.stu = User.objects.create_user("TSTU3", "Start@1234", full_name="Stu", role=Role.STUDENT)
        StudentProfile.objects.create(user=self.stu, branch=Branch.objects.create(name="Test2", code="TS2"), year_of_study=1)

    def as_user(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def lesson(self, area, section, kind, prompt="Do it", options=None):
        g = Guide.objects.create(area=area, section=section, kind="NOTES", title=f"{kind} lesson", body="x")
        r = self.as_user(self.admin).put(f"{API}/guides/{g.pk}/task-setting/", {"task_type": kind, "prompt": prompt, "options": options or []}, format="json")
        self.assertEqual(r.status_code, 200, getattr(r, "data", None))
        return g

    def submit(self, g, data):
        return self.as_user(self.stu).post(f"{API}/guides/{g.pk}/submit/", data, format="multipart")

    def test_select_needs_listed_choices_and_a_reason(self):
        g = self.lesson("CAREER", "technologies", "SELECT", options=["Python", "SQL", "React"])
        self.assertEqual(self.submit(g, {"choices": ["Java"], "text": "I like it very much"}).status_code, 400)
        self.assertEqual(self.submit(g, {"choices": ["Python"], "text": "no"}).status_code, 400)
        r = self.submit(g, {"choices": ["Python", "SQL"], "text": "Python and SQL are used everywhere"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["choices"], ["Python", "SQL"])
        self.assertTrue(r.data["lesson_completed"])

    def test_select_task_needs_two_items(self):
        g = Guide.objects.create(area="CAREER", section="technologies", kind="NOTES", title="t", body="x")
        r = self.as_user(self.admin).put(f"{API}/guides/{g.pk}/task-setting/", {"task_type": "SELECT", "options": ["only one"]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_checklist_needs_every_item(self):
        g = self.lesson("CAREER", "roadmap", "CHECKLIST", options=["A", "B"])
        self.assertEqual(self.submit(g, {"choices": ["A"]}).status_code, 400)
        r = self.submit(g, {"choices": ["A", "B"]})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertTrue(r.data["lesson_completed"])

    def test_code_and_link_tasks(self):
        c = self.lesson("JOB_PREP", "coding", "CODE")
        self.assertEqual(self.submit(c, {"text": "x"}).status_code, 400)
        self.assertEqual(self.submit(c, {"text": "def f(s):\n    return s == s[::-1]"}).status_code, 201)
        u = self.lesson("CAREER", "projects", "URL")
        self.assertEqual(self.submit(u, {"link": "not a link"}).status_code, 400)
        r = self.submit(u, {"link": "https://github.com/me/tracker", "text": "Tracks attendance"})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["link"], "https://github.com/me/tracker")

    def test_voice_and_text_needs_both(self):
        g = self.lesson("COMM", "gd", "VOICE_TEXT")
        r = self.submit(g, {"text": "My two points are cost and distraction."})
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(r.data["lesson_completed"])  # still needs the recording
        rec = self.as_user(self.stu).post(f"{API}/recordings/", {"guide_id": g.pk, "seconds": 5,
                                          "file": SimpleUploadedFile("a.webm", b"\x1aE\xdf\xa3audio", content_type="audio/webm")}, format="multipart")
        self.assertEqual(rec.status_code, 201, getattr(rec, "data", None))
        self.assertTrue(GuideDone.objects.filter(user=self.stu, guide=g).exists())


class QuizEngineTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("QADM", "Start@1234", full_name="Admin", role=Role.ADMIN)
        self.stu = User.objects.create_user("QSTU", "Start@1234", full_name="Stu", role=Role.STUDENT)
        StudentProfile.objects.create(user=self.stu, branch=Branch.objects.create(name="Test3", code="TS3"), year_of_study=1)
        self.g = Guide.objects.create(area="JOB_PREP", section="aptitude", kind="NOTES", title="Simple Interest", body="x")

    def as_user(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_numeric_and_mcq_are_graded_and_answers_hidden(self):
        a = self.as_user(self.admin)
        m = a.post(f"{API}/guide-questions/", {"guide_id": self.g.pk, "qtype": "MCQ", "text": "SI on 1000 at 5% for 2 years?", "options": ["50", "100", "150", "200"], "correct": 1}, format="json")
        n = a.post(f"{API}/guide-questions/", {"guide_id": self.g.pk, "qtype": "NUMERIC", "text": "SI on 2500 at 8% for 3 years?", "answer": "600"}, format="json")
        self.assertEqual(m.status_code, 201, m.data)
        self.assertEqual(n.status_code, 201, n.data)
        bad = a.post(f"{API}/guide-questions/", {"guide_id": self.g.pk, "qtype": "NUMERIC", "text": "x", "answer": "abc"}, format="json")
        self.assertEqual(bad.status_code, 400)
        s = self.as_user(self.stu)
        qs = s.get(f"{API}/guides/{self.g.pk}/quiz/").data["questions"]
        self.assertNotIn("correct", qs[0])
        self.assertNotIn("answer", qs[1])
        self.assertEqual(qs[1]["options"], [])
        ans = {str(qs[0]["id"]): 1, str(qs[1]["id"]): "600.0"}
        r = s.post(f"{API}/guides/{self.g.pk}/quiz/", {"answers": ans, "seconds": 42, "timed": True}, format="json")
        self.assertEqual(r.data["score"], 2, r.data)
        self.assertEqual(r.data["accuracy"], 100)
        wrong = s.post(f"{API}/guides/{self.g.pk}/quiz/", {"answers": {str(qs[0]["id"]): 0, str(qs[1]["id"]): "5"}}, format="json")
        self.assertEqual(wrong.data["score"], 0)
        perf = s.get(f"{API}/quiz-performance/?area=JOB_PREP&section=aptitude").data
        self.assertEqual(perf["attempts"], 2)
        self.assertEqual(perf["accuracy"], 50)
        self.assertEqual(perf["topics"][0]["best"], 100)

    def test_faculty_cannot_use_student_quiz(self):
        fac = User.objects.create_user("QFAC", "Start@1234", full_name="Fac", role=Role.FACULTY)
        self.assertEqual(self.as_user(fac).get(f"{API}/guides/{self.g.pk}/quiz/").status_code, 403)


class NoticeTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("NADM", "Start@1234", full_name="Admin", role=Role.ADMIN)
        self.stu = User.objects.create_user("NSTU", "Start@1234", full_name="Stu", role=Role.STUDENT)
        self.fac = User.objects.create_user("NFAC", "Start@1234", full_name="Fac", role=Role.FACULTY)

    def as_user(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_new_lesson_notifies_students_only_and_can_be_marked_read(self):
        r = self.as_user(self.admin).post(f"{API}/guides/", {"area": "COMM", "section": "spoken", "kind": "NOTES", "title": "Greetings", "body": "Hello", "order_no": 0}, format="multipart")
        self.assertEqual(r.status_code, 201, getattr(r, "data", None))
        s = self.as_user(self.stu)
        got = [n for n in s.get(f"{API}/notices/").data if n["title"] != "Lessons waiting for you"]
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["text"], "Greetings")
        self.assertEqual(got[0]["link"], "/student/communication/spoken")
        self.assertEqual(self.as_user(self.fac).get(f"{API}/notices/").data, [])
        s.post(f"{API}/notices/read/")
        self.assertTrue(all(n["read"] for n in s.get(f"{API}/notices/").data))

    def test_feedback_notifies_the_student(self):
        g = Guide.objects.create(area="CAREER", section="paths", kind="NOTES", title="Paths", body="x")
        from academics.tracking import GuideSubmission, Notice
        Notice.objects.all().delete()
        sub = GuideSubmission.objects.create(user=self.stu, guide=g, text="my answer is long enough here")
        r = self.as_user(self.fac).patch(f"{API}/guide-submissions/{sub.pk}/", {"feedback": "Well done"}, format="json")
        self.assertEqual(r.status_code, 200, getattr(r, "data", None))
        n = self.as_user(self.stu).get(f"{API}/notices/").data
        self.assertIn("Feedback on your task", [x["title"] for x in n])

    def test_daily_reminder_for_lessons_not_completed(self):
        g = Guide.objects.create(area="JOB_PREP", section="aptitude", kind="NOTES", title="Percentages", body="x")
        from academics.tracking import Notice
        Notice.objects.all().delete()
        s = self.as_user(self.stu)
        got = [n for n in s.get(f"{API}/notices/").data if n["title"] == "Lessons waiting for you"]
        self.assertEqual(len(got), 1)
        again = [n for n in s.get(f"{API}/notices/").data if n["title"] == "Lessons waiting for you"]
        self.assertEqual(len(again), 1)  # only one a day
        GuideDone.objects.create(user=self.stu, guide=g)
        Notice.objects.all().delete()
        self.assertEqual([n for n in s.get(f"{API}/notices/").data if n["title"] == "Lessons waiting for you"], [])

    def test_mark_one_notice_read(self):
        from academics.tracking import Notice
        a = Notice.objects.create(user=self.stu, title="A")
        b = Notice.objects.create(user=self.stu, title="B")
        s = self.as_user(self.stu)
        s.post(f"{API}/notices/read/", {"id": a.pk}, format="json")
        a.refresh_from_db(); b.refresh_from_db()
        self.assertTrue(a.read)
        self.assertFalse(b.read)
        other = User.objects.create_user("NSTU2", "Start@1234", full_name="O", role=Role.STUDENT)
        self.as_user(other).post(f"{API}/notices/read/", {"id": b.pk}, format="json")
        b.refresh_from_db()
        self.assertFalse(b.read)  # nobody can mark another user's notice


class StudentReportTests(TestCase):
    def setUp(self):
        self.fac = User.objects.create_user("RFAC", "Start@1234", full_name="Fac", role=Role.FACULTY)
        self.stu = User.objects.create_user("RSTU", "Start@1234", full_name="Rita Student", role=Role.STUDENT)
        self.g = Guide.objects.create(area="JOB_PREP", section="aptitude", kind="NOTES", title="Percentages", body="x")
        GuideQuestion.objects.create(guide=self.g, text="q", option_a="1", option_b="2", option_c="3", option_d="4", correct=1)

    def test_faculty_sees_one_students_report_and_students_cannot(self):
        f = APIClient()
        f.force_authenticate(self.fac)
        r = f.get(f"{API}/performance/student/{self.stu.pk}/")
        self.assertEqual(r.status_code, 200, getattr(r, "data", None))
        self.assertEqual(r.data["student"]["name"], "Rita Student")
        job = [a for a in r.data["learning"] if a["area"] == "JOB_PREP"][0]
        self.assertEqual((job["lessons"], job["completed"], job["quiz_attempts"]), (1, 0, 0))
        s = APIClient()
        s.force_authenticate(self.stu)
        self.assertEqual(s.post(f"{API}/guides/{self.g.pk}/quiz/", {"answers": {}}, format="json").status_code, 200)
        self.assertEqual(s.get(f"{API}/performance/student/{self.stu.pk}/").status_code, 403)
        again = f.get(f"{API}/performance/student/{self.stu.pk}/").data
        self.assertEqual([a for a in again["learning"] if a["area"] == "JOB_PREP"][0]["quiz_attempts"], 1)
        self.assertEqual(f.get(f"{API}/performance/student/999999/").status_code, 404)
