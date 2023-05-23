"""Multi-status test charm for OP033 spec.."""

import logging

import ops
from statusprioritizer import StatusPrioritizer

logger = logging.getLogger(__name__)


class StatustestCharm(ops.CharmBase):
    """Status test charm."""

    def __init__(self, *args):
        super().__init__(*args)

        self.database = Database(self)
        self.webapp = Webapp(self)

        self.prioritizer = StatusPrioritizer()
        self.prioritizer.add("database", self.database.get_status)
        self.prioritizer.add("webapp", self.webapp.get_status)
        self.framework.observe(self.framework.on.commit, self._on_commit)

    def _on_commit(self, event):
        self.unit.status = self.prioritizer.highest_prefixed()


class Database(ops.Object):
    """Database component."""

    def __init__(self, charm):
        super().__init__(charm, "database")

        self.charm = charm
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        if "database_mode" not in self.charm.model.config:
            return
        mode = self.charm.model.config["database_mode"]
        logger.info("Using database mode %r", mode)

    def get_status(self) -> ops.StatusBase:
        """Return this component's status."""
        if "database_mode" not in self.charm.model.config:
            return ops.BlockedStatus('"database_mode" required')
        return ops.ActiveStatus()


class Webapp(ops.Object):
    """Web app component."""

    def __init__(self, charm):
        super().__init__(charm, "webapp")

        self.charm = charm
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

    def _on_config_changed(self, event):
        if "webapp_port" not in self.charm.model.config:
            return
        port = self.charm.model.config["webapp_port"]
        logger.info("Using web app port %r", port)

    def get_status(self) -> ops.StatusBase:
        """Return this component's status."""
        if "webapp_port" not in self.charm.model.config:
            return ops.BlockedStatus('"webapp_port" required')
        return ops.ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    ops.main(StatustestCharm)
