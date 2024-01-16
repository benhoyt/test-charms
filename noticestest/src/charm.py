#!/usr/bin/env python3
"""Charm to test Pebble Notices."""

import logging

import ops

logger = logging.getLogger(__name__)


class _FakeS3Bucket:
    def upload_fileobj(self, f, key):
        content = f.read()
        logger.info(f"Would upload {len(content)} bytes to key {key!r}")


s3_bucket = _FakeS3Bucket()


class PostgresCharm(ops.CharmBase):
    """Charm to test Pebble Notices."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        # Note that "db" is the workload container's name
        framework.observe(self.on["db"].pebble_custom_notice, self._on_pebble_custom_notice)

    def _on_pebble_custom_notice(self, event: ops.PebbleCustomNoticeEvent) -> None:
        if event.notice.key == "canonical.com/postgresql/backup-done":
            path = event.notice.last_data["path"]
            logger.info("Backup finished, copying %s to the cloud", path)
            f = event.workload.pull(path, encoding=None)
            s3_bucket.upload_fileobj(f, "db-backup.sql")

        elif event.notice.key == "canonical.com/postgresql/other-thing":
            logger.info("Handling other thing")


if __name__ == "__main__":  # pragma: nocover
    ops.main(PostgresCharm)  # type: ignore
