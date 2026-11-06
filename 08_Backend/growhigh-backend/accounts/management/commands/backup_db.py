"""Back up the PostgreSQL database (and optionally uploaded files) into the backups/ folder.

Run:   python manage.py backup_db
       python manage.py backup_db --with-media --keep 14
Needs PostgreSQL's pg_dump. If it is not on your PATH, set PG_BIN in .env, e.g.
       PG_BIN=C:\\Program Files\\PostgreSQL\\17\\bin
Each run creates backups/growhigh_YYYYMMDD_HHMMSS.dump and deletes the oldest ones beyond --keep (default 14).
Restore with:  python manage.py restore_db --file backups/growhigh_....dump
"""
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


def pg_tool(name):
    """Full path of a PostgreSQL command line tool, from PG_BIN or the PATH."""
    folder = os.getenv("PG_BIN", "").strip().strip('"')
    if folder:
        for cand in (Path(folder) / name, Path(folder) / f"{name}.exe"):
            if cand.exists():
                return str(cand)
    found = shutil.which(name)
    if not found:
        raise CommandError(f"{name} not found. Add PostgreSQL's bin folder to PATH or set PG_BIN in .env.")
    return found


def db_env():
    db = settings.DATABASES["default"]
    env = dict(os.environ)
    env["PGPASSWORD"] = str(db.get("PASSWORD") or "")
    args = ["-h", str(db.get("HOST") or "localhost"), "-p", str(db.get("PORT") or "5432"), "-U", str(db.get("USER") or "postgres")]
    return db["NAME"], args, env


class Command(BaseCommand):
    help = "Back up the database (and optionally uploaded files) into the backups folder"

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=14, help="how many backups to keep (default 14)")
        parser.add_argument("--with-media", action="store_true", help="also zip the media folder (uploaded videos, PDFs, audio)")
        parser.add_argument("--folder", default=str(settings.BASE_DIR / "backups"))

    def handle(self, *args, **opts):
        folder = Path(opts["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        name, conn, env = db_env()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = folder / f"growhigh_{stamp}.dump"
        cmd = [pg_tool("pg_dump"), *conn, "-Fc", "-f", str(out), name]
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            out.unlink(missing_ok=True)
            raise CommandError(f"pg_dump failed: {result.stderr.strip() or result.stdout.strip()}")
        self.stdout.write(self.style.SUCCESS(f"Database saved: {out} ({out.stat().st_size // 1024} KB)"))
        if opts["with_media"] and Path(settings.MEDIA_ROOT).exists():
            archive = shutil.make_archive(str(folder / f"media_{stamp}"), "zip", settings.MEDIA_ROOT)
            self.stdout.write(self.style.SUCCESS(f"Uploaded files saved: {archive}"))
        for pattern in ("growhigh_*.dump", "media_*.zip"):
            old = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)[max(opts["keep"], 1):]
            for f in old:
                f.unlink()
                self.stdout.write(f"Removed old backup {f.name}")
