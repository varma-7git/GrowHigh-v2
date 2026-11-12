from exams.models import Attempt, AttemptAnswer, Question
from exams.tests import ExamsBase, mk_question


class RescoreTests(ExamsBase):
    def test_changing_the_correct_option_re_marks_old_results(self):
        self.client.force_authenticate(self.fac)
        qid = self.client.post("/api/v1/questions/", mk_question(self.topic.pk), format="json").data["id"]
        att = Attempt.objects.create(student=self.s1, total=1, submitted_at="2026-11-01T10:00:00Z")
        AttemptAnswer.objects.create(attempt=att, question_id=qid, selected=2, is_correct=False)
        att.score = 0
        att.save()
        r = self.client.patch(f"/api/v1/questions/{qid}/", {"correct": 2}, format="json")
        self.assertEqual(r.status_code, 200, getattr(r, "data", None))
        att.refresh_from_db()
        self.assertEqual(att.score, 1)
        self.assertTrue(AttemptAnswer.objects.get(attempt=att).is_correct)
        self.client.patch(f"/api/v1/questions/{qid}/", {"text": "Reworded"}, format="json")  # other edits change nothing
        att.refresh_from_db()
        self.assertEqual(att.score, 1)
