"""Load multiple-choice questions from a JSON file into every branch that has the subject.

Run:  python manage.py import_questions --file seed/questions_C23_core.json
Safe to run again: a question with the same text under the same topic is skipped.

File format:
{
  "regulation": "C23",
  "questions": [
    {"subject": "Operating Systems", "topic": "Process", "text": "...", "options": ["a", "b", "c", "d"], "correct": 1, "explanation": "..."}
  ]
}
"subject" must match a subject name exactly. "topic" is matched by part of the topic name; if it is missing the subject's first topic is used, and if it
does not match any topic of a branch's version of the subject the question is skipped for that branch (topic lists differ
between branches). The question is added to that subject in every branch of the regulation.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from academics.models import Subject
from common.constants import Role
from exams.models import Question


class Command(BaseCommand):
    help = "Import multiple-choice questions for existing subjects from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True)

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        reg = data["regulation"].strip().upper()
        from accounts.models import User
        owner = User.objects.filter(role=Role.ADMIN, is_active=True).order_by("id").first()
        added = skipped = unmatched = 0
        missing = set()
        for q in data["questions"]:
            opts_ = q["options"]
            if len(opts_) != 4 or len(set(opts_)) != 4 or q["correct"] not in (0, 1, 2, 3):
                raise CommandError(f"Bad question: {q['text'][:60]}")
            subjects = list(Subject.objects.filter(name=q["subject"], regulation__code=reg))
            if not subjects:
                missing.add(q["subject"])
                continue
            for subj in subjects:
                topics = list(subj.topics.order_by("order_no", "id"))
                if not topics:
                    continue
                key = (q.get("topic") or "").lower()
                topic = next((t for t in topics if key in t.name.lower()), None) if key else topics[0]
                if topic is None:
                    unmatched += 1
                    continue
                if Question.objects.filter(topic=topic, text=q["text"]).exists():
                    skipped += 1
                    continue
                Question.objects.create(
                    topic=topic, text=q["text"], option_a=opts_[0], option_b=opts_[1], option_c=opts_[2], option_d=opts_[3],
                    correct=q["correct"], explanation=q.get("explanation", ""), created_by=owner)
                added += 1
        for m in sorted(missing):
            self.stdout.write(self.style.WARNING(f"No subject named '{m}' in {reg}: run import_curriculum first."))
        self.stdout.write(self.style.SUCCESS(f"Done. Added {added} questions, skipped {skipped} duplicates, {unmatched} did not fit a branch's topics."))
