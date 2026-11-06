"""Restore the database from a backup made by backup_db. This REPLACES the current data.

Run:  python manage.py restore_db --file backups/growhigh_20261102_200000.dump --yes
Without --yes it asks for confirmation. Stop runserver first so no one is using the database.
"""
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from .backup_db import db_env, pg_tool


class Command(BaseCommand):
    help = "Restore the database from a .dump file (replaces current data)"

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True)
        parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        name, conn, env = db_env()
        if not opts["yes"]:
            answer = input(f"This will replace ALL data in database '{name}'. Type yes to continue: ")
            if answer.strip().lower() != "yes":
                self.stdout.write("Cancelled. Nothing was changed.")
                return
        cmd = [pg_tool("pg_restore"), *conn, "-d", name, "--clean", "--if-exists", "--no-owner", str(path)]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode not in (0, 1):  # 1 = finished with harmless warnings
            raise CommandError(f"pg_restore failed: {result.stderr.strip()}")
        self.stdout.write(self.style.SUCCESS(f"Database restored from {path.name}."))
        if result.returncode == 1 and result.stderr.strip():
            self.stdout.write(self.style.WARNING("Finished with warnings:\n" + result.stderr.strip()[:1500]))
