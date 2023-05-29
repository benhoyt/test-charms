"""Multi-status test charm for OP033 spec.."""

import logging
import typing

import multistatus
import ops

logger = logging.getLogger(__name__)


class StatustestCharm(ops.CharmBase):
    """Status test charm."""

    def __init__(self, *args):
        super().__init__(*args)
        self.database = Database(self)
        self.webapp = Webapp(self)
        self.prioritizer = multistatus.Prioritizer()
        self.prioritizer.add("database", self.database.get_status)
        self.prioritizer.add("webapp", self.webapp.get_status)
        self.framework.observe(self.framework.on.commit, self._on_commit)

    def _on_commit(self, event):
        self.unit.status = self.prioritizer.highest()


class Database(ops.Object):
    """Database component."""

    def __init__(self, charm):
        super().__init__(charm, "database")
        self.charm = charm
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

    def get_status(self) -> ops.StatusBase:
        """Return this component's status."""
        status = self._validate_config()
        return status if status is not None else ops.ActiveStatus()

    def _validate_config(self) -> typing.Optional[ops.StatusBase]:
        """Validate charm config for the database component.

        Return a status if the config is incorrect, None if it's valid.
        """
        if "database_mode" not in self.charm.model.config:
            return ops.BlockedStatus('"database_mode" required')
        return None

    def _on_config_changed(self, event):
        if self._validate_config() is not None:
            return
        mode = self.charm.model.config["database_mode"]
        logger.info("Using database mode %r", mode)


class Webapp(ops.Object):
    """Web app component."""

    def __init__(self, charm):
        super().__init__(charm, "webapp")
        self.charm = charm
        charm.framework.observe(charm.on.config_changed, self._on_config_changed)

    def get_status(self) -> ops.StatusBase:
        """Return this component's status."""
        status = self._validate_config()
        return status if status is not None else ops.ActiveStatus()

    def _validate_config(self) -> typing.Optional[ops.StatusBase]:
        """Validate charm config for the web app component.

        Return a status if the config is incorrect, None if it's valid.
        """
        if "webapp_port" not in self.charm.model.config:
            return ops.BlockedStatus('"webapp_port" required')
        return None

    def _on_config_changed(self, event):
        if self._validate_config() is not None:
            return
        port = self.charm.model.config["webapp_port"]
        logger.info("Using web app port %r", port)


if __name__ == "__main__":  # pragma: nocover
    ops.main(StatustestCharm)
