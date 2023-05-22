"""Multi-status test charm for OP033 spec.."""

import logging

import ops
import statuspool

logger = logging.getLogger(__name__)


class StatustestCharm(ops.CharmBase):
    """Status test charm."""

    def __init__(self, *args):
        super().__init__(*args)

        status_pool = statuspool.StatusPool(self)
        self.database = Database(self, status_pool)
        self.webapp = Webapp(self, status_pool)


class Database(ops.Object):
    """Database component."""

    def __init__(self, charm, status_pool):
        super().__init__(charm, "database")

        self.charm = charm
        self.status = statuspool.Status("database")
        status_pool.add(self.status)
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

        self._update_config()

    def _on_config_changed(self, event):
        self._update_config()

    def _update_config(self):
        if "database_mode" not in self.charm.model.config:
            self.status.set(ops.BlockedStatus('"database_mode" required'))
            return

        mode = self.charm.model.config["database_mode"]
        logger.info("Using database mode %r", mode)
        self.status.set(ops.ActiveStatus(f"db mode {mode!r}"))


class Webapp(ops.Object):
    """Web app component."""

    def __init__(self, charm, status_pool):
        super().__init__(charm, "webapp")

        self.charm = charm
        self.status = statuspool.Status("webapp")
        status_pool.add(self.status)
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

        self._update_config()

    def _on_config_changed(self, event):
        self._update_config()

    def _update_config(self):
        if "webapp_port" not in self.charm.model.config:
            self.status.set(ops.BlockedStatus('"webapp_port" required'))
            return

        port = self.charm.model.config["webapp_port"]
        logger.info("Using web app port %r", port)
        self.status.set(ops.ActiveStatus(f"web app port {port!r}"))


if __name__ == "__main__":  # pragma: nocover
    ops.main(StatustestCharm)
