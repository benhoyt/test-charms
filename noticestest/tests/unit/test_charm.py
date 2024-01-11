import unittest
from unittest.mock import patch

import ops
import ops.testing
from charm import PostgresCharm


class TestCharm(unittest.TestCase):
    @patch("charm.s3_bucket.upload_fileobj")
    def test_backup_done(self, upload_fileobj):
        harness = ops.testing.Harness(PostgresCharm)
        self.addCleanup(harness.cleanup)
        harness.begin()
        harness.set_can_connect("db", True)

        # Pretend backup file has been written
        root = harness.get_filesystem_root("db")
        (root / "tmp").mkdir()
        (root / "tmp" / "mydb.sql").write_text("BACKUP")

        # Notify to record the notice and fire the event
        harness.pebble_notify(
            "db", "canonical.com/postgresql/backup-done", data={"path": "/tmp/mydb.sql"}
        )

        # Ensure backup content was "uploaded" to S3
        upload_fileobj.assert_called_once()
        upload_f, upload_key = upload_fileobj.call_args.args
        self.assertEqual(upload_f.read(), b"BACKUP")
        self.assertEqual(upload_key, "db-backup.sql")
