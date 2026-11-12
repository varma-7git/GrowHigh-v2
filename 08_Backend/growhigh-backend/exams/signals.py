"""When faculty change which option is correct, re-mark every submitted attempt that used that question."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Attempt, AttemptAnswer, Question


def rescore_question(question):
    """Re-mark answers to this question and refresh the score of each submitted attempt it touches."""
    touched = set()
    for a in AttemptAnswer.objects.filter(question=question, attempt__submitted_at__isnull=False):
        ok = a.selected is not None and a.selected == question.correct
        if ok != a.is_correct:
            a.is_correct = ok
            a.save(update_fields=["is_correct"])
            touched.add(a.attempt_id)
    for att in Attempt.objects.filter(pk__in=touched):
        att.score = att.answers.filter(is_correct=True).count()
        att.save(update_fields=["score"])
    return len(touched)


@receiver(pre_save, sender=Question)
def _remember_correct(sender, instance, **kwargs):
    old = Question.objects.filter(pk=instance.pk).values_list("correct", flat=True).first() if instance.pk else None
    instance._old_correct = old


@receiver(post_save, sender=Question)
def _rescore_on_change(sender, instance, created, **kwargs):
    if not created and getattr(instance, "_old_correct", None) not in (None, instance.correct):
        rescore_question(instance)
