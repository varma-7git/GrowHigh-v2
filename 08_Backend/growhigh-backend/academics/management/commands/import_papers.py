"""Add many previous-year paper PDFs at once from a folder.

Name each file  YEAR_BRANCH_Title.pdf  where BRANCH is a branch code (CSE, ECE ...) or ALL for every branch, and Title is optional:
    2023_ALL.pdf              -> "AP ECET 2023"
    2023_CSE.pdf              -> "AP ECET 2023 · CSE"
    2024_CSE_Paper 1.pdf      -> "Paper 1"
Run:  python manage.py import_papers --folder C:\\papers
Safe to run again: a paper with the same year, branch and title is skipped.
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from academics.models import Branch
from exams.models import Paper


class Command(BaseCommand):
    help = "Import previous-year paper PDFs from a folder"

    def add_arguments(self, parser):
        parser.add_argument("--folder", required=True)

    def handle(self, *args, **opts):
        folder = Path(opts["folder"])
        if not folder.is_dir():
            raise CommandError(f"Folder not found: {folder}")
        added = skipped = 0
        for f in sorted(folder.glob("*.pdf")):
            parts = f.stem.split("_", 2)
            if len(parts) < 2 or not parts[0].isdigit():
                self.stdout.write(self.style.WARNING(f"Skipped {f.name}: name it YEAR_BRANCH_Title.pdf"))
                skipped += 1
                continue
            year, code = int(parts[0]), parts[1].strip()
            branch = None
            if code.upper() != "ALL":
                try:
                    branch = Branch.objects.get(code__iexact=code)
                except Branch.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Skipped {f.name}: no branch with code {code}"))
                    skipped += 1
                    continue
            title = parts[2].strip() if len(parts) == 3 and parts[2].strip() else f"AP ECET {year}{f' · {branch.code}' if branch else ''}"
            if Paper.objects.filter(year=year, branch=branch, title=title).exists():
                skipped += 1
                continue
            with f.open("rb") as fh:
                p = Paper(year=year, branch=branch, title=title)
                p.file.save(f.name, File(fh), save=True)
            added += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Added {added} papers, skipped {skipped}."))
