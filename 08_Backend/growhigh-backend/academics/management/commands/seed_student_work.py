"""Demo students DEMO-STU2 and DEMO-STU3 do practice questions and hands-on tasks through the real API.

    py manage.py seed_student_work

Run it after seed_full_demo, seed_lessons and seed_aptitude. Run it once: it skips a lesson a student has already attempted.
Voice recordings are not created (there is no real audio to record), so lessons that need a recording stay unfinished.
"""
from django.core.management.base import BaseCommand
from rest_framework.test import APIClient

from academics.models import Guide
from academics.tracking import GuideQuestion, GuideQuizAttempt
from accounts.models import User

API = "/api/v1"

# Each entry: lesson title -> what STU2 and STU3 hand in. Keys: text, link, choices (positions in the lesson's list).
WORK = {
    "Percentages": (
        {"text": "Price after 15% off: 1200 x 0.85 = Rs 1,020. Tax 5% of 1,020 = Rs 51. Final price = 1,020 + 51 = Rs 1,071."},
        {"text": "15% of 1200 is 180 so the bag costs 1020. Then 5% tax is 51 so I pay 1071 rupees."}),
    "Simple Interest": (
        {"text": "Loan: Rs 20,000 at 6% for 2 years. SI = 20000 x 6 x 2 / 100 = Rs 2,400, amount = Rs 22,400. For 3 years SI = Rs 3,600, so the interest grows by Rs 1,200 for each extra year."},
        {"text": "Principal 10000, rate 5 percent, time 2 years. SI = 10000 x 5 x 2 / 100 = 1000. Total amount is 11000."}),
    "Compound Interest": (
        {"text": "Simple interest: 10000 x 8 x 3 / 100 = 2,400, amount 12,400. Compound: 10000 x 1.08^3 = 12,597.12, so CI = 2,597.12. Compound gives Rs 197.12 more."},
        {"text": "SI for 3 years is 2400 so amount is 12400. For compound interest I did 10000 x 1.08 x 1.08 x 1.08 = 12597. Difference is about 197 rupees."}),
    "Time and Work": (
        {"text": "Pipe A fills in 12 h: 1/12 per hour. Pipe B fills in 6 h: 1/6 per hour. Together 1/12 + 2/12 = 3/12 = 1/4 per hour, so the tank fills in 4 hours."},
        {"text": "Pipe A does 1/12 and pipe B does 1/6 in one hour. Add them: 1/12 + 2/12 = 3/12. So it takes 4 hours."}),
    "Alphabet Series": (
        {"text": "1) C, F, I, L, ? Rule +3 positions, next O, R. 2) Z, W, T, Q, ? Rule -3, next N, K. 3) A, B, D, G, ? Gaps 1, 2, 3, 4 so next K, P."},
        {"text": "Series 1: B D F H, rule +2, next J L. Series 2: Z Y X W, rule -1, next V U. Series 3: A C F J, gaps rise by 1, next O U."}),
    "Strings in Python: reverse and palindrome": (
        {"text": "def is_palindrome(s):\n    t = s.replace(' ', '').lower()\n    return t == t[::-1]\n\nis_palindrome('Nitin') -> True\nis_palindrome('Never odd or even') -> True"},
        {"text": "def is_palindrome(s):\n    s = s.lower().replace(' ', '')\n    return s == s[::-1]\n\nprint(is_palindrome('madam'))  # True\nprint(is_palindrome('hello'))  # False"}),
    "Lists and loops: finding the largest number": (
        {"text": "def second_largest(nums):\n    first = second = None\n    for n in nums:\n        if first is None or n > first:\n            second = first\n            first = n\n        elif n != first and (second is None or n > second):\n            second = n\n    return second\n\nIt keeps the two largest values while looping once through the list."},
        {"text": "def second_largest(nums):\n    big = max(nums)\n    best = None\n    for n in nums:\n        if n != big and (best is None or n > best):\n            best = n\n    return best\n\nFirst I find the biggest, then the biggest of the rest."}),
    "SQL basics: SELECT, WHERE and GROUP BY": (
        {"text": "(a) SELECT name FROM students WHERE branch = 'CSE' AND marks > 60;\n(b) SELECT branch, COUNT(*) FROM students GROUP BY branch;"},
        {"text": "SELECT name FROM students WHERE branch = 'CSE' AND marks > 60;\nSELECT branch, COUNT(*) FROM students GROUP BY branch;"}),
    "Choosing your first technology to learn": (
        {"choices": [0, 1, 5], "text": "I chose Python, SQL and Django because they fit together for building web apps with a database, which is what I want to build for my final project."},
        {"choices": [2, 3], "text": "I want HTML & CSS and JavaScript first because I like making web pages that I can see working."}),
    "Career paths after a diploma": (
        {"choices": [2, 3], "text": "I will write AP ECET for lateral entry into B.Tech. Next: finish ECET practice papers, then apply for counselling, and build one project during the course."},
        {"choices": [0], "text": "I want to join a private company after my diploma. Next I will make a resume, learn SQL and apply to openings."}),
    "Stage 1: Fundamentals": (
        {"choices": [0, 1, 2, 3, 4], "text": ""},
        {"choices": [0, 1, 2, 3, 4], "text": ""}),
    "Stage 3: Apply and interview": (
        {"choices": [0, 1, 2, 3, 4], "text": ""},
        None),
    "Project idea: Student attendance tracker": (
        {"link": "https://github.com/demo-student-2/attendance-tracker", "text": "A Django app where faculty mark attendance for each subject and a student sees the attendance percentage per subject."},
        None),
    "Present and past tense": (
        {"text": "1) She goes to college every day. 2) Yesterday I watched a movie. 3) They are studying now. 4) He doesn't like tea."},
        {"text": "1) She goes to college every day. 2) Yesterday I watched a movie. 3) They are studying now. 4) He don't like tea."}),
    "Words for the workplace": (
        {"text": "I met my colleague before the deadline. We took feedback from our manager. My schedule was full that day. I am responsible for testing. The deadline was extended after the review."},
        {"text": "My colleague helped me finish before the deadline. The manager gave feedback on my work. I made a schedule for the week. I am responsible for my own tasks."}),
    "Writing a professional email": (
        {"text": "Subject: Application for internship in software development\n\nDear Sir/Madam,\n\nI am a diploma student in Computer Engineering and I am writing to ask about internship openings in your company.\n\nI have built a small attendance tracker in Python and SQL, and I am keen to learn from a real project team. I am available for three months after my exams.\n\nPlease let me know if you need my resume or any other detail. Thank you for your time.\n\nYours faithfully,\nDemo Student 2"},
        {"text": "Subject: Internship\n\nDear Sir,\n\nI want to ask if you have internship. I am diploma student and I know python.\n\nPlease reply me.\n\nThank you\nDemo Student 3"}),
}


class Command(BaseCommand):
    help = "Demo students DEMO-STU2 and DEMO-STU3 do lesson practice questions and hands-on tasks."

    def handle(self, *args, **opts):
        for who, idx in (("DEMO-STU2", 0), ("DEMO-STU3", 1)):
            user = User.objects.filter(login_id=who).first()
            if not user:
                self.stdout.write(self.style.WARNING(f"{who} not found. Run seed_full_demo first."))
                continue
            c = APIClient(HTTP_HOST="localhost")
            c.force_authenticate(user)
            quizzes = tasks = 0
            guides = list(Guide.objects.filter(is_active=True, area__in=["JOB_PREP", "CAREER", "COMM"]).order_by("area", "section", "order_no", "id"))
            n = 0
            for g in guides:
                qs = list(GuideQuestion.objects.filter(guide=g))
                if qs and not GuideQuizAttempt.objects.filter(user=user, guide=g).exists() and (idx == 0 or n % 2 == 0):
                    first_try_poor = idx == 1 and n % 4 == 0
                    for attempt in (["poor", "good"] if first_try_poor else ["good" if idx == 0 else "mixed"]):
                        ans = {}
                        for i, q in enumerate(qs):
                            right = (attempt == "good" and i % 6 != 5) or (attempt == "mixed" and i % 2 == 0)
                            if q.qtype == "NUMERIC":
                                ans[str(q.id)] = q.answer if right else str(float(q.answer) + 1)
                            else:
                                ans[str(q.id)] = q.correct if right else (q.correct + 1) % 4
                        r = c.post(f"{API}/guides/{g.id}/quiz/", {"answers": ans, "seconds": 40 + 25 * len(qs), "timed": idx == 0}, format="json")
                        if r.status_code != 200:
                            self.stdout.write(self.style.ERROR(f"{who} quiz {g.title}: {r.status_code} {getattr(r, 'data', '')}"))
                    quizzes += 1
                    n += 1
                work = WORK.get(g.title)
                work = work[idx] if work else None
                if work:
                    info = c.get(f"{API}/guide-tasks/?area={g.area}&section={g.section}").data.get(str(g.id), {})
                    opts_ = info.get("options", [])
                    body = {"text": work.get("text", "")}
                    if work.get("link"):
                        body["link"] = work["link"]
                    if "choices" in work:
                        body["choices"] = [opts_[i] for i in work["choices"] if i < len(opts_)]
                    if info.get("type") in ("RECORDING", "VOICE_TEXT") and info.get("type") == "RECORDING":
                        continue
                    r = c.post(f"{API}/guides/{g.id}/submit/", body, format="multipart")
                    if r.status_code == 201:
                        tasks += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"{who} task {g.title}: {r.status_code} {getattr(r, 'data', '')}"))
            self.stdout.write(self.style.SUCCESS(f"{who}: practised {quizzes} lessons, submitted {tasks} tasks."))
