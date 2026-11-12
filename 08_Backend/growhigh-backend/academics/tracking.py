"""Lesson questions (quiz), automatic completion and the Career growth tracker.

A lesson is never ticked by hand. A lesson can have two parts and completes when every part it has is done:
  * Practice questions (optional): score 40% or more.
  * Hands-on task (every lesson has one, about the lesson's own topic):
      RECORDING - Communication / Speaking prompts: save a spoken answer
      WRITTEN   - write an answer (the default)
      UPLOAD    - upload a file (a project, a document, a screenshot)
Faculty and admin see the written answers and uploads and can leave feedback.
"""
from decimal import Decimal, InvalidOperation

from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import parsers, serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Guide, GuideDone, Recording
from .views import IsAdminOrFaculty, IsAdminRole, IsStudentRole

PASS_PERCENT = 40


# ---------- models
class GuideQuestion(models.Model):
    """One practice question on a lesson: multiple choice (exactly one correct option) or a numerical answer."""
    class Kind(models.TextChoices):
        MCQ = "MCQ", "Multiple choice"
        NUMERIC = "NUMERIC", "Numerical answer"

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="questions")
    qtype = models.CharField(max_length=7, choices=Kind.choices, default=Kind.MCQ)
    text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=300, blank=True, default="")
    option_b = models.CharField(max_length=300, blank=True, default="")
    option_c = models.CharField(max_length=300, blank=True, default="")
    option_d = models.CharField(max_length=300, blank=True, default="")
    correct = models.PositiveSmallIntegerField(default=0)  # MCQ: 0 = A ... 3 = D
    answer = models.CharField(max_length=40, blank=True, default="")  # NUMERIC: the correct number
    explanation = models.TextField(blank=True, default="")
    order_no = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = "academics"
        ordering = ["order_no", "id"]

    @property
    def options(self):
        return [self.option_a, self.option_b, self.option_c, self.option_d] if self.qtype == "MCQ" else []

    def is_right(self, given):
        """True when the student's answer is right. Numbers match to two decimal places."""
        if self.qtype == "NUMERIC":
            try:
                return abs(Decimal(str(given).strip().replace(",", "")) - Decimal(self.answer)) <= Decimal("0.01")
            except (InvalidOperation, ValueError, TypeError):
                return False
        return isinstance(given, int) and not isinstance(given, bool) and given == self.correct

    @property
    def correct_text(self):
        return self.answer if self.qtype == "NUMERIC" else f"{'ABCD'[self.correct]}. {self.options[self.correct]}"


class GuideTaskSetting(models.Model):
    """What the student does for a lesson that has no questions. No row means: Speaking prompts are recorded, everything else is written."""
    class Type(models.TextChoices):
        WRITTEN = "WRITTEN", "Write an answer"
        UPLOAD = "UPLOAD", "Upload a file"
        RECORDING = "RECORDING", "Record a spoken answer"
        SELECT = "SELECT", "Choose from a list and explain"
        CHECKLIST = "CHECKLIST", "Tick every step on a checklist"
        CODE = "CODE", "Write code"
        URL = "URL", "Share a link (GitHub or other)"
        VOICE_TEXT = "VOICE_TEXT", "Record and also write an answer"

    guide = models.OneToOneField(Guide, on_delete=models.CASCADE, related_name="task_setting")
    task_type = models.CharField(max_length=10, choices=Type.choices, default=Type.WRITTEN)
    prompt = models.TextField(blank=True, default="")
    options = models.JSONField(default=list, blank=True)  # the list for SELECT and CHECKLIST tasks

    class Meta:
        app_label = "academics"


class GuideSubmission(models.Model):
    """A student's written answer or uploaded file for a lesson. One per student and lesson; sending again replaces it."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="guide_submissions")
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True, default="")
    file = models.FileField(upload_to="submissions/%Y/%m/", blank=True, default="")
    choices = models.JSONField(default=list, blank=True)  # what the student picked or ticked
    link = models.URLField(max_length=500, blank=True, default="")
    feedback = models.TextField(blank=True, default="")
    reviewed_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "academics"
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["user", "guide"], name="unique_guide_submission")]


class GuideQuizResult(models.Model):
    """A student's best result on a lesson's practice questions."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="guide_quiz_results")
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="quiz_results")
    percent = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "academics"
        constraints = [models.UniqueConstraint(fields=["user", "guide"], name="unique_guide_quiz_result")]


class GuideQuizAttempt(models.Model):
    """Every time a student submits a lesson's practice questions. Feeds accuracy and topic-wise performance."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="guide_quiz_attempts")
    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name="quiz_attempts")
    correct = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    seconds = models.PositiveIntegerField(default=0)
    timed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "academics"
        ordering = ["-created_at"]


class Notice(models.Model):
    """A notification for one user, kept on the server so it reaches them on any device."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="notices")
    title = models.CharField(max_length=150)
    text = models.CharField(max_length=300, blank=True, default="")
    link = models.CharField(max_length=200, blank=True, default="")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "academics"
        ordering = ["-created_at", "-id"]


class CareerGoal(models.Model):
    """A goal a student tracks in Career growth: learn a technology, finish a project, apply for a role."""
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        DONE = "DONE", "Done"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="career_goals")
    title = models.CharField(max_length=150)
    target_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "academics"
        ordering = ["-created_at"]


# ---------- notices
SILENT = False  # the seed commands set this so loading demo lessons does not flood students with notices
AREA_PATH = {"JOB_PREP": "/student/job-prep", "CAREER": "/student/career", "COMM": "/student/communication"}
AREA_NAME = {"JOB_PREP": "Job preparation", "CAREER": "Career growth", "COMM": "Communication"}


@receiver(post_save, sender=Guide)
def _notify_students_of_new_lesson(sender, instance, created, raw=False, **kwargs):
    if not created or raw or SILENT or not instance.is_active or instance.area not in AREA_PATH:
        return
    from accounts.models import User
    from common.constants import Role
    link = f"{AREA_PATH[instance.area]}/{instance.section}"
    Notice.objects.bulk_create([
        Notice(user_id=uid, title=f"New lesson in {AREA_NAME[instance.area]}", text=instance.title[:300], link=link)
        for uid in User.objects.filter(role=Role.STUDENT, is_active=True).values_list("id", flat=True)])


# ---------- a saved recording completes its speaking prompt
@receiver(post_save, sender=Recording)
def _recording_completes_lesson(sender, instance, created, **kwargs):
    if created and instance.guide_id:
        try_complete(instance.user, instance.guide)


# ---------- serializers
class GuideQuestionSerializer(serializers.ModelSerializer):
    guide_id = serializers.PrimaryKeyRelatedField(source="guide", queryset=Guide.objects.all())
    options = serializers.ListField(child=serializers.CharField(max_length=300, allow_blank=True), required=False)

    class Meta:
        model = GuideQuestion
        fields = ["id", "guide_id", "qtype", "text", "options", "correct", "answer", "explanation", "order_no"]

    def validate(self, data):
        kind = data.get("qtype", getattr(self.instance, "qtype", "MCQ"))
        if kind == "NUMERIC":
            try:
                Decimal(str(data.get("answer", getattr(self.instance, "answer", ""))).strip())
            except InvalidOperation:
                raise serializers.ValidationError({"answer": "Enter the correct answer as a number."})
            data["answer"] = str(data.get("answer", getattr(self.instance, "answer", ""))).strip()
            data["options"] = ["", "", "", ""]
            data["correct"] = 0
        elif self.instance is not None and "options" not in data and "correct" not in data:
            return data
        else:
            opts = [v.strip() for v in data.get("options", [])]
            if len(opts) != 4 or any(not v for v in opts) or len({v.lower() for v in opts}) < 4:
                raise serializers.ValidationError({"options": "Fill four different options."})
            if data.get("correct", 0) not in (0, 1, 2, 3):
                raise serializers.ValidationError({"correct": "Pick the correct option: A, B, C or D."})
            data["options"] = opts
            data["answer"] = ""
        return data

    def _apply(self, data):
        opts = data.pop("options", None)
        if opts:
            data["option_a"], data["option_b"], data["option_c"], data["option_d"] = opts
        return data

    def create(self, data):
        return GuideQuestion.objects.create(**self._apply(data))

    def update(self, instance, data):
        for k, v in self._apply(data).items():
            setattr(instance, k, v)
        instance.save()
        return instance


class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerGoal
        fields = ["id", "title", "target_date", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


# ---------- views
class GuideQuestionViewSet(viewsets.ModelViewSet):
    """Admin writes the questions of a lesson. GET /guide-questions/?guide=<id>"""
    serializer_class = GuideQuestionSerializer
    permission_classes = [IsAdminRole]
    queryset = GuideQuestion.objects.all()
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        qs = GuideQuestion.objects.all()
        g = self.request.query_params.get("guide", "")
        return qs.filter(guide_id=int(g)) if g.isdigit() else qs


class QuizCountsView(APIView):
    """GET /guide-quiz-counts/?area=JOB_PREP&section=aptitude  ->  {"<guide id>": question count}"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = GuideQuestion.objects.filter(guide__is_active=True)
        p = request.query_params
        if p.get("area"):
            qs = qs.filter(guide__area=p["area"])
        if p.get("section"):
            qs = qs.filter(guide__section=p["section"])
        out = {}
        for gid in qs.values_list("guide_id", flat=True):
            out[str(gid)] = out.get(str(gid), 0) + 1
        return Response(out)


class GuideQuizView(APIView):
    """GET /guides/<id>/quiz/ gives the questions without answers. POST {"answers": {"<question id>": 0-3}} grades them."""
    permission_classes = [IsStudentRole]

    def get(self, request, pk):
        qs = GuideQuestion.objects.filter(guide_id=pk, guide__is_active=True)
        return Response({"questions": [{"id": q.id, "qtype": q.qtype, "text": q.text, "options": q.options} for q in qs]})

    def post(self, request, pk):
        qs = list(GuideQuestion.objects.filter(guide_id=pk, guide__is_active=True))
        if not qs:
            return Response({"detail": "This lesson has no questions."}, status=400)
        answers = request.data.get("answers")
        answers = {str(k): v for k, v in answers.items()} if isinstance(answers, dict) else {}
        review, score = [], 0
        for q in qs:
            sel = answers.get(str(q.id))
            ok = q.is_right(sel) if sel not in (None, "") else False
            score += 1 if ok else 0
            review.append({"id": q.id, "qtype": q.qtype, "text": q.text, "options": q.options, "correct_text": q.correct_text,
                           "selected": sel if sel not in (None, "") else None, "is_correct": ok, "explanation": q.explanation})
        percent = round(score * 100 / len(qs))
        passed = percent >= PASS_PERCENT
        try:
            seconds = max(0, min(int(request.data.get("seconds") or 0), 86400))
        except (TypeError, ValueError):
            seconds = 0
        with transaction.atomic():
            GuideQuizAttempt.objects.create(user=request.user, guide_id=pk, correct=score, total=len(qs), seconds=seconds, timed=bool(request.data.get("timed")))
            res, _ = GuideQuizResult.objects.get_or_create(user=request.user, guide_id=pk)
            res.percent, res.passed = max(res.percent, percent), res.passed or passed
            res.save()
        completed = try_complete(request.user, qs[0].guide)
        return Response({"score": score, "total": len(qs), "percent": percent, "accuracy": percent, "seconds": seconds, "passed": passed,
                         "lesson_completed": completed, "review": review})


class QuizPerformanceView(APIView):
    """GET /quiz-performance/?area=JOB_PREP&section=aptitude -> the signed-in student's results, topic by topic."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        p = request.query_params
        guides = Guide.objects.filter(is_active=True, questions__isnull=False).distinct()
        if p.get("area"):
            guides = guides.filter(area=p["area"])
        if p.get("section"):
            guides = guides.filter(section=p["section"])
        guides = list(guides.order_by("order_no", "id"))
        by = {}
        for a in GuideQuizAttempt.objects.filter(user=request.user, guide__in=guides).order_by("created_at"):
            by.setdefault(a.guide_id, []).append(a)
        topics, tc, tt = [], 0, 0
        for g in guides:
            at = by.get(g.id, [])
            c, t = sum(a.correct for a in at), sum(a.total for a in at)
            tc, tt = tc + c, tt + t
            best = max((round(a.correct * 100 / a.total) for a in at if a.total), default=None)
            topics.append({"guide_id": g.id, "title": g.title, "attempts": len(at), "best": best,
                           "last": round(at[-1].correct * 100 / at[-1].total) if at and at[-1].total else None,
                           "accuracy": round(c * 100 / t) if t else None})
        return Response({"attempts": sum(len(v) for v in by.values()), "accuracy": round(tc * 100 / tt) if tt else None,
                         "topics_total": len(guides), "topics_attempted": len(by), "topics": topics})


class NoticeView(APIView):
    """GET /notices/ lists the signed-in user's latest notices. POST /notices/read/ marks them all read."""
    permission_classes = [IsAuthenticated]

    REMIND = "Lessons waiting for you"

    def remind(self, user):
        """Once a day, tell a student how many lessons they have not completed yet."""
        from django.utils import timezone
        from common.constants import Role
        if user.role != Role.STUDENT or Notice.objects.filter(user=user, title=self.REMIND, created_at__date=timezone.localdate()).exists():
            return
        done = set(GuideDone.objects.filter(user=user).values_list("guide_id", flat=True))
        left = {}
        for gid, area in Guide.objects.filter(is_active=True, area__in=AREA_PATH).values_list("id", "area"):
            if gid not in done:
                left[area] = left.get(area, 0) + 1
        if not left:
            return
        first = max(left, key=left.get)
        text = ", ".join(f"{AREA_NAME[a]} {n}" for a, n in left.items())
        Notice.objects.create(user=user, title=self.REMIND, text=f"{sum(left.values())} not completed yet: {text}"[:300], link=AREA_PATH[first])

    def get(self, request):
        self.remind(request.user)
        rows = Notice.objects.filter(user=request.user)[: 200 if request.query_params.get("all") else 30]
        return Response([{"id": n.id, "title": n.title, "text": n.text, "link": n.link, "read": n.read, "at": n.created_at} for n in rows])

    def post(self, request):
        """Marks every notice read, or only the one in {"id": n}."""
        qs = Notice.objects.filter(user=request.user, read=False)
        one = request.data.get("id")
        if one is not None:
            qs = qs.filter(pk=one) if str(one).isdigit() else qs.none()
        qs.update(read=True)
        return Response({"ok": True})


class StudentReportView(APIView):
    """GET /performance/student/<id>/ - one student's whole picture for faculty and admin: test results, weak topics and
    progress in Job preparation, Career growth and Communication. Faculty and admin see results from every test."""
    permission_classes = [IsAdminOrFaculty]

    def get(self, request, pk):
        from collections import defaultdict
        from common.constants import Role
        from exams.models import Attempt, AttemptAnswer, Test
        from accounts.models import User
        from rest_framework.exceptions import NotFound
        try:
            stu = User.objects.get(pk=pk, role=Role.STUDENT)
        except User.DoesNotExist:
            raise NotFound("Student not found.")
        pct = lambda a, b: round(a * 100 / b) if b else None
        # ---- tests
        tests = Test.objects.all()
        done = list(Attempt.objects.filter(student=stu, test__in=tests, submitted_at__isnull=False).select_related("test").order_by("-submitted_at"))
        topics = defaultdict(lambda: [0, 0])
        for row in AttemptAnswer.objects.filter(attempt__in=[a.id for a in done]).select_related("question__topic"):
            t = topics[row.question.topic.name]
            t[1] += 1
            t[0] += 1 if row.is_correct else 0
        weak = sorted(({"name": n, "percent": pct(c, t), "answers": t} for n, (c, t) in topics.items()), key=lambda x: x["percent"])
        results = [{"name": a.test.name, "date": a.test.scheduled_date, "score": a.score, "total": a.total, "percent": pct(a.score, a.total),
                    "passed": (pct(a.score, a.total) or 0) >= PASS_PERCENT} for a in done]
        practice = list(Attempt.objects.filter(student=stu, test__isnull=True, submitted_at__isnull=False))
        assigned = sum(t.assignments.filter(student=stu).count() for t in tests)
        avg = round(sum(r["percent"] for r in results) / len(results)) if results else None
        # ---- lessons
        guides = list(Guide.objects.filter(is_active=True, area__in=AREA_PATH).values("id", "area", "title"))
        finished = set(GuideDone.objects.filter(user=stu).values_list("guide_id", flat=True))
        quiz = defaultdict(lambda: [0, 0, 0])  # attempts, correct, total
        per_lesson = {}
        for a in GuideQuizAttempt.objects.filter(user=stu):
            q = quiz[a.guide_id]
            q[0] += 1; q[1] += a.correct; q[2] += a.total
        subs = list(GuideSubmission.objects.filter(user=stu).select_related("guide"))
        recs = list(Recording.objects.filter(user=stu).select_related("guide"))
        areas = []
        for area in ("JOB_PREP", "CAREER", "COMM"):
            gs = [g for g in guides if g["area"] == area]
            ids = {g["id"] for g in gs}
            att = sum(quiz[i][0] for i in ids if i in quiz)
            cor = sum(quiz[i][1] for i in ids if i in quiz)
            tot = sum(quiz[i][2] for i in ids if i in quiz)
            ss = [x for x in subs if x.guide.area == area]
            rr = [x for x in recs if x.guide_id in ids]
            areas.append({"area": area, "label": AREA_NAME[area], "lessons": len(gs), "completed": len([i for i in ids if i in finished]),
                          "quiz_attempts": att, "accuracy": pct(cor, tot), "submissions": len(ss) + len(rr),
                          "waiting": len([x for x in ss if not x.reviewed_by_id]) + len([x for x in rr if not x.reviewed_by_id])})
        titles = {g["id"]: g["title"] for g in guides}
        weak_lessons = sorted(({"title": titles[i], "attempts": q[0], "accuracy": pct(q[1], q[2])} for i, q in quiz.items() if i in titles and q[2]), key=lambda x: x["accuracy"])[:5]
        recent = sorted(
            [{"title": x.guide.title, "type": "Written/upload", "at": x.updated_at, "reviewed": bool(x.reviewed_by_id), "feedback": x.feedback} for x in subs]
            + [{"title": (x.guide.title if x.guide_id else "Spoken answer"), "type": "Spoken", "at": x.created_at, "reviewed": bool(x.reviewed_by_id), "feedback": x.feedback} for x in recs],
            key=lambda r: r["at"], reverse=True)[:8]
        return Response({
            "student": {"id": stu.id, "name": stu.full_name, "login_id": stu.login_id},
            "tests": {"assigned": assigned, "taken": len(results), "average": avg, "pass_rate": round(sum(1 for r in results if r["passed"]) * 100 / len(results)) if results else None,
                      "results": results[:10], "weak_topics": weak[:6], "practice_sets": len(practice),
                      "practice_average": round(sum(pct(a.score, a.total) or 0 for a in practice) / len(practice)) if practice else None},
            "learning": areas, "weak_lessons": weak_lessons, "recent": recent,
        })


class CareerGoalViewSet(viewsets.ModelViewSet):
    """A student's own goals."""
    serializer_class = CareerGoalSerializer
    permission_classes = [IsStudentRole]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return CareerGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---------- tasks: what the student does for each lesson
DEFAULT_PROMPT = "Write a short answer in your own words: what did you learn, and how would you use it? (at least 20 characters)"
UPLOAD_EXT = (".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".zip", ".mp4", ".webm", ".mov", ".mp3", ".m4a")
SPOKEN_AREAS = ("COMM", "JOB_PREP")  # lessons where a recording is allowed
MAX_UPLOAD_MB = 25


def task_for(guide):
    """(type, prompt) of the hands-on task for this lesson."""
    cfg = getattr(guide, "task_setting", None)
    if cfg:
        return cfg.task_type, cfg.prompt or ("Record your answer to this prompt." if cfg.task_type in ("RECORDING", "VOICE_TEXT") else DEFAULT_PROMPT)
    if guide.area == "COMM" and guide.section == "speaking":
        return "RECORDING", "Record your answer to this prompt."
    return "WRITTEN", DEFAULT_PROMPT


def try_complete(user, guide):
    """Mark the lesson done when its practice questions are passed (if it has any) and its hands-on task is done."""
    if GuideQuestion.objects.filter(guide=guide).exists() and not GuideQuizResult.objects.filter(user=user, guide=guide, passed=True).exists():
        return False
    kind, _ = task_for(guide)
    has_rec = Recording.objects.filter(user=user, guide=guide).exists()
    has_sub = GuideSubmission.objects.filter(user=user, guide=guide).exists()
    task_done = has_rec if kind == "RECORDING" else (has_rec and has_sub) if kind == "VOICE_TEXT" else has_sub
    if task_done:
        GuideDone.objects.get_or_create(user=user, guide=guide)
    return task_done


class SubmissionSerializer(serializers.ModelSerializer):
    guide_id = serializers.IntegerField(read_only=True)
    guide_title = serializers.CharField(source="guide.title", read_only=True)
    student_name = serializers.CharField(source="user.full_name", read_only=True)
    login_id = serializers.CharField(source="user.login_id", read_only=True)
    file_url = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    task_type = serializers.SerializerMethodField()

    class Meta:
        model = GuideSubmission
        fields = ["id", "guide_id", "guide_title", "task_type", "student_name", "login_id", "text", "choices", "link", "file_url", "feedback", "reviewed_by_name", "updated_at"]
        read_only_fields = ["text", "choices", "link"]

    def get_file_url(self, o):
        if not o.file:
            return ""
        req = self.context.get("request")
        return req.build_absolute_uri(o.file.url) if req else o.file.url

    def get_reviewed_by_name(self, o):
        return o.reviewed_by.full_name if o.reviewed_by_id else ""

    def get_task_type(self, o):
        return task_for(o.guide)[0]


class GuideTasksView(APIView):
    """GET /guide-tasks/?area=JOB_PREP&section=aptitude -> {"<guide id>": {"type", "prompt", "questions", "submission"}} for the signed-in student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        p = request.query_params
        guides = Guide.objects.filter(is_active=True).select_related("task_setting")
        if p.get("area"):
            guides = guides.filter(area=p["area"])
        if p.get("section"):
            guides = guides.filter(section=p["section"])
        guides = list(guides)
        counts = {}
        for gid in GuideQuestion.objects.filter(guide__in=guides).values_list("guide_id", flat=True):
            counts[gid] = counts.get(gid, 0) + 1
        mine = {s.guide_id: s for s in GuideSubmission.objects.filter(user=request.user, guide__in=guides).select_related("reviewed_by")}
        quiz = {r.guide_id: r for r in GuideQuizResult.objects.filter(user=request.user, guide__in=guides)}
        out = {}
        for g in guides:
            kind, prompt = task_for(g)
            sub = mine.get(g.id)
            q = quiz.get(g.id)
            cfg = getattr(g, "task_setting", None)
            out[str(g.id)] = {"type": kind, "prompt": prompt, "options": (cfg.options if cfg else []), "questions": counts.get(g.id, 0),
                              "quiz_best": q.percent if q else None, "quiz_passed": bool(q and q.passed),
                              "submission": SubmissionSerializer(sub, context={"request": request}).data if sub else None}
        return Response(out)


class GuideTaskSettingView(APIView):
    """Admin: GET or PUT /guides/<id>/task-setting/ {"task_type": "WRITTEN|UPLOAD|RECORDING", "prompt": "..."}"""
    permission_classes = [IsAdminRole]

    def get(self, request, pk):
        cfg = GuideTaskSetting.objects.filter(guide_id=pk).first()
        return Response({"task_type": cfg.task_type if cfg else "", "prompt": cfg.prompt if cfg else "", "options": cfg.options if cfg else []})

    def put(self, request, pk):
        kind = request.data.get("task_type")
        if kind not in GuideTaskSetting.Type.values:
            return Response({"detail": "Choose a task type.", "errors": {"task_type": ["Choose a task type."]}}, status=400)
        guide = Guide.objects.filter(pk=pk).first()
        if not guide:
            return Response({"detail": "Lesson not found."}, status=404)
        if kind in ("RECORDING", "VOICE_TEXT") and guide.area not in SPOKEN_AREAS:
            return Response({"detail": "Recording is only for Communication and Job preparation lessons.", "errors": {"task_type": ["Recording is only for Communication and Job preparation lessons."]}}, status=400)
        raw = request.data.get("options", [])
        if isinstance(raw, str):
            raw = raw.splitlines()
        options = [str(o).strip()[:100] for o in (raw or []) if str(o).strip()][:20]
        if kind in ("SELECT", "CHECKLIST") and len(options) < 2:
            return Response({"detail": "Add at least two items, one per line.", "errors": {"options": ["Add at least two items, one per line."]}}, status=400)
        if kind not in ("SELECT", "CHECKLIST"):
            options = []
        prompt = str(request.data.get("prompt", ""))[:1000]
        GuideTaskSetting.objects.update_or_create(guide=guide, defaults={"task_type": kind, "prompt": prompt, "options": options})
        return Response({"task_type": kind, "prompt": prompt, "options": options})


class GuideSubmitView(APIView):
    """Student: POST /guides/<id>/submit/ (multipart or JSON) with text and/or file. Completes the lesson."""
    permission_classes = [IsStudentRole]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def post(self, request, pk):
        guide = Guide.objects.filter(pk=pk, is_active=True).first()
        if not guide:
            return Response({"detail": "Lesson not found."}, status=404)
        kind, _ = task_for(guide)
        if kind == "RECORDING":
            return Response({"detail": "This lesson's task is a spoken answer. Record it instead."}, status=400)
        text = str(request.data.get("text", "")).strip()
        file = request.FILES.get("file")
        link = str(request.data.get("link", "")).strip()
        raw = request.data.getlist("choices") if hasattr(request.data, "getlist") else request.data.get("choices", [])
        picked = [str(c) for c in (raw or [])]
        cfg = getattr(guide, "task_setting", None)
        options = list(cfg.options) if cfg else []

        def bad(field, msg):
            return Response({"detail": msg, "errors": {field: [msg]}}, status=400)

        if kind in ("WRITTEN", "VOICE_TEXT") and len(text) < 20:
            return bad("text", "Write at least 20 characters.")
        if kind == "CODE" and len(text) < 15:
            return bad("text", "Paste or write your code (at least 15 characters).")
        if kind == "SELECT":
            if not picked or any(c not in options for c in picked):
                return bad("choices", "Choose at least one item from the list.")
            if len(text) < 10:
                return bad("text", "Explain your choice in at least 10 characters.")
        if kind == "CHECKLIST" and set(picked) != set(options):
            return bad("choices", "Tick every item on the checklist.")
        if kind == "URL" and not (link.lower().startswith(("http://", "https://")) and "." in link and " " not in link):
            return bad("link", "Enter a full link starting with http:// or https://")
        if kind == "UPLOAD":
            if not file:
                return bad("file", "Choose a file to upload.")
            if not file.name.lower().endswith(UPLOAD_EXT):
                return bad("file", "Upload a PDF, Word, text, image, audio, video or ZIP file.")
            if file.size > MAX_UPLOAD_MB * 1024 * 1024:
                return bad("file", f"The file must be {MAX_UPLOAD_MB} MB or smaller.")
        sub, _ = GuideSubmission.objects.get_or_create(user=request.user, guide=guide)
        sub.text = text
        sub.choices = picked if kind in ("SELECT", "CHECKLIST") else []
        sub.link = link if kind == "URL" else ""
        if file:
            sub.file = file
        sub.feedback, sub.reviewed_by = "", None  # a new answer needs new feedback
        sub.save()
        completed = try_complete(request.user, guide)
        return Response({**SubmissionSerializer(sub, context={"request": request}).data, "lesson_completed": completed}, status=201)


class GuideSubmissionViewSet(viewsets.ModelViewSet):
    """Faculty and admin read the answers and uploads and leave feedback. GET /guide-submissions/?guide=<id>&pending=1"""
    serializer_class = SubmissionSerializer
    permission_classes = [IsAdminOrFaculty]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = GuideSubmission.objects.select_related("user", "guide", "reviewed_by")
        p = self.request.query_params
        if p.get("guide", "").isdigit():
            qs = qs.filter(guide_id=int(p["guide"]))
        if p.get("pending") in ("1", "true"):
            qs = qs.filter(reviewed_by__isnull=True)
        return qs

    def perform_update(self, serializer):
        sub = serializer.save(reviewed_by=self.request.user)
        if sub.feedback:
            Notice.objects.create(user_id=sub.user_id, title="Feedback on your task", text=f"{sub.guide.title}: {sub.feedback}"[:300],
                                  link=f"{AREA_PATH.get(sub.guide.area, '/student')}/{sub.guide.section}")
