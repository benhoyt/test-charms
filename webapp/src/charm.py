#!/usr/bin/env python3
"""Webapp charm to test secrets consumer."""

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class WebAppCharm(CharmBase):
    """Webapp charm to test secrets consumer."""

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.db_relation_changed, self._on_db_relation_changed)
        self.framework.observe(self.on.secret_changed, self._on_secret_changed)

    def _on_db_relation_changed(self, event):
        relation_data = event.relation.data[event.app]
        logger.info(f"_on_db_relation_changed: {event.relation} data={relation_data}")
        if "db_password_id" not in event.relation.data[event.app]:
            event.defer()
            return
        secret_id = event.relation.data[event.app]["db_password_id"]
        secret = self.model.get_secret(id=secret_id, label="db_password")
        content = secret.get_content()
        # NOTE: Don't log the secret content for real charms!
        logger.info(f"would update web app {secret} with new content {content}")
        self.unit.status = ActiveStatus("relation-changed: would update web app's db secret")

    def _on_secret_changed(self, event):
        logger.info(f"_on_secret_changed: {event.secret}")
        if event.secret.label == "db_password":
            # could try out latest password with event.secret.peek() and block if bad
            old_content = event.secret.get_content()
            content = event.secret.get_content(refresh=True)
            if content == old_content:
                self.unit.status = ActiveStatus("secret-changed: secret content not changed")
                return

            # NOTE: Don't log the secret content for real charms!
            logger.info(f"would update web app {event.secret} with new content {content}")
            self.unit.status = ActiveStatus("secret-changed: would update web app's db secret")


if __name__ == "__main__":  # pragma: nocover
    main(WebAppCharm)
