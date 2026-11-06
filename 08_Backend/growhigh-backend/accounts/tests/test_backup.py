import tempfile
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class BackupTests(TestCase):
    def _fake_run(self, cmd, **kw):
        Path(cmd[cmd.index("-f") + 1]).write_bytes(b"PGDMP fake")
        return mock.Mock(returncode=0, stderr="", stdout="")

    @mock.patch("accounts.management.commands.backup_db.pg_tool", return_value="pg_dump")
    def test_backup_creates_file_and_keeps_only_latest(self, _tool):
        import time
        with tempfile.TemporaryDirectory() as d, mock.patch("subprocess.run", side_effect=self._fake_run):
            for _ in range(3):
                call_command("backup_db", folder=d, keep=2)
                time.sleep(1.1)  # file names carry the second
            self.assertEqual(len(list(Path(d).glob("growhigh_*.dump"))), 2)

    @mock.patch("accounts.management.commands.backup_db.pg_tool", return_value="pg_dump")
    def test_failed_dump_leaves_no_file(self, _tool):
        bad = mock.Mock(returncode=1, stderr="connection refused", stdout="")
        with tempfile.TemporaryDirectory() as d, mock.patch("subprocess.run", return_value=bad):
            with self.assertRaises(CommandError):
                call_command("backup_db", folder=d)
            self.assertEqual(list(Path(d).glob("*.dump")), [])

    def test_restore_needs_existing_file(self):
        with self.assertRaises(CommandError):
            call_command("restore_db", file="nope.dump", yes=True)
