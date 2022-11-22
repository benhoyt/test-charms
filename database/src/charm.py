#!/usr/bin/env python3
"""Database charm to test secrets owner."""

import datetime
import logging
import random

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, SecretRotate

logger = logging.getLogger(__name__)


class DatabaseCharm(CharmBase):
    """Database charm to test secrets owner."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.db_relation_created, self._on_db_relation_created)
        self.framework.observe(self.on.db_relation_broken, self._on_db_relation_broken)
        self.framework.observe(self.on.secret_rotate, self._on_secret_rotate)
        self.framework.observe(self.on.secret_remove, self._on_secret_remove)
        self.framework.observe(self.on.secret_expired, self._on_secret_expired)

    def _generate_secret_content(self):
        n = random.randrange(100)
        password = f"pass{n}"
        logger.info(f"would update database with new password {password!r}")
        return {"password": password}

    def _on_db_relation_created(self, event):
        logger.info(f"_on_db_relation_created: {event.relation}")
        content = self._generate_secret_content()
        secret = self.app.add_secret(
            content,
            label="password",
            rotate=SecretRotate.HOURLY,
            expire=datetime.timedelta(hours=2),
        )
        secret.grant(event.relation)
        event.relation.data[self.app]["db_password_id"] = secret.id
        self.unit.status = ActiveStatus(f"created {secret} with content {content}")

    def _on_db_relation_broken(self, event):
        logger.info(f"_on_db_relation_broken: {event.relation}")
        secret = self.model.get_secret(label="password")
        secret.remove_all()  # grants also revoked by Juju
        self.unit.status = ActiveStatus(f"removed {secret}")

    def _on_secret_rotate(self, event):
        logger.info(f"_on_secret_rotate: {event.secret}")
        if event.secret.label == "password":
            content = self._generate_secret_content()
            event.secret.set_content(content)
            self.unit.status = ActiveStatus(f"set {event.secret} content {content}")

    def _on_secret_remove(self, event):  # remove unused revision early
        logger.info(f"_on_secret_remove: {event.secret}")
        if event.secret.label == "password":
            event.secret.remove_revision()
            self.unit.status = ActiveStatus(f"removed secret revision {event.secret}")

    def _on_secret_expired(self, event):
        logger.info(f"_on_secret_expired: {event.secret}")
        if event.secret.label == "password":
            event.secret.remove_revision()
            self.unit.status = ActiveStatus(f"removed secret revision {event.secret}")


if __name__ == "__main__":  # pragma: nocover
    main(DatabaseCharm)
