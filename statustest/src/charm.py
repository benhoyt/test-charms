"""Multi-status test charm for OP033 spec."""

import logging

import multistatus
import ops

logger = logging.getLogger(__name__)


class StatustestCharm(ops.CharmBase):
    """Status test charm."""

    def __init__(self, *args):
        super().__init__(*args)

        status_group = multistatus.Group(self)
        self.database = Database(self, status_group)
        self.webapp = Webapp(self, status_group)


class Database(ops.Object):
    """Database component."""

    def __init__(self, charm, status_group):
        super().__init__(charm, "database")

        self.charm = charm
        self.component = multistatus.Component(status_group, "database")
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

        self._update_config()

    def _on_config_changed(self, event):
        self._update_config()

    def _update_config(self):
        if "database_mode" not in self.charm.model.config:
            self.component.status = ops.BlockedStatus('"database_mode" required')
            return

        mode = self.charm.model.config["database_mode"]
        logger.info("Using database mode %r", mode)
        self.component.status = ops.ActiveStatus(f"db mode {mode!r}")


class Webapp(ops.Object):
    """Web app component."""

    def __init__(self, charm, status_group):
        super().__init__(charm, "webapp")

        self.charm = charm
        self.component = multistatus.Component(status_group, "webapp")
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

        self._update_config()

    def _on_config_changed(self, event):
        self._update_config()

    def _update_config(self):
        if "webapp_port" not in self.charm.model.config:
            self.component.status = ops.BlockedStatus('"webapp_port" required')
            return

        port = self.charm.model.config["webapp_port"]
        logger.info("Using web app port %r", port)
        self.component.status = ops.ActiveStatus(f"web app port {port!r}")


if __name__ == "__main__":  # pragma: nocover
    ops.main(StatustestCharm)
