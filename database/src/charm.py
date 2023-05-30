#!/usr/bin/env python3
"""Database charm to test secrets owner."""

import datetime
import logging
import random
import typing

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, SecretRotate
from ops.charm import (
    RelationBrokenEvent,
    RelationCreatedEvent,
    SecretExpiredEvent,
    SecretRemoveEvent,
    SecretRotateEvent,
)

logger = logging.getLogger(__name__)


class DatabaseCharm(CharmBase):
    """Database charm to test secrets owner."""

    def __init__(self, *args: typing.Any):
        super().__init__(*args)
        self.framework.observe(self.on["db"].relation_created, self._on_db_relation_created)
        self.framework.observe(self.on["db"].relation_broken, self._on_db_relation_broken)
        self.framework.observe(self.on.secret_rotate, self._on_secret_rotate)
        self.framework.observe(self.on.secret_remove, self._on_secret_remove)
        self.framework.observe(self.on.secret_expired, self._on_secret_expired)

    def _generate_secret_content(self) -> typing.Dict[str, str]:
        n = random.randrange(100)
        password = f"pass{n}"
        # NOTE: Don't log the secret content for real charms!
        logger.info(f"would update database with new password {password!r}")
        return {"password": password}

    def _on_db_relation_created(self, event: RelationCreatedEvent):
        logger.info(f"_on_db_relation_created: {event.relation}")
        content = self._generate_secret_content()
        secret = self.app.add_secret(
            content,
            label="password",
            rotate=SecretRotate.HOURLY,
            expire=datetime.timedelta(hours=2),
        )
        assert secret.id is not None
        secret.grant(event.relation)
        event.relation.data[self.app]["db_password_id"] = secret.id
        self.unit.status = ActiveStatus("relation-created: added new secret")

    def _on_db_relation_broken(self, event: RelationBrokenEvent):
        logger.info(f"_on_db_relation_broken: {event.relation}")
        secret = self.model.get_secret(label="password")
        secret.remove_all_revisions()  # grants also revoked by Juju
        self.unit.status = ActiveStatus("relation-broken: removed secret")

    def _on_secret_rotate(self, event: SecretRotateEvent):
        logger.info(f"_on_secret_rotate: {event.secret}")
        if event.secret.label == "password":
            content = self._generate_secret_content()
            event.secret.set_content(content)
            self.unit.status = ActiveStatus("secret-rotate: updated secret content")

    def _on_secret_remove(self, event: SecretRemoveEvent):  # remove unused revision early
        logger.info(f"_on_secret_remove: {event.secret}")
        if event.secret.label == "password":
            event.secret.remove_revision(event.revision)
            self.unit.status = ActiveStatus("secret-remove: removed secret revision")

    def _on_secret_expired(self, event: SecretExpiredEvent):
        logger.info(f"_on_secret_expired: {event.secret}")
        if event.secret.label == "password":
            event.secret.remove_revision(event.revision)
            self.unit.status = ActiveStatus("secret-expired: removed secret revision")


if __name__ == "__main__":  # pragma: nocover
    main(DatabaseCharm)
