"""Status prioritizer."""

import typing

import ops


class Prioritizer:
    """Status prioritizer: track the highest-priority status among several components."""

    _PRIORITIES = {
        "error": 0,
        "blocked": 1,
        "waiting": 2,
        "maintenance": 3,
        "active": 4,
        "unknown": 5,
    }

    def __init__(self):
        self._components = {}

    def add(self, component: str, get_status: typing.Callable[[], ops.StatusBase]):
        """Add a named status component."""
        if component in self._components:
            raise ValueError(f"duplicate component {component!r}")
        self._components[component] = get_status

    def highest(self) -> ops.StatusBase:
        """Return highest-priority status with message prefixed with component name."""
        statuses = self.all()
        if not statuses:
            return ops.ActiveStatus()
        component, status = statuses[0]
        if isinstance(status, ops.ActiveStatus) and not status.message:
            return ops.ActiveStatus()
        return ops.StatusBase.from_name(status.name, f"[{component}] {status.message}")

    def all(self) -> list[tuple[str, ops.StatusBase]]:
        """Return list of (component_name, status) tuples for all components.

        The list is ordered highest-priority first. If there are two statuses
        with the same level, components added first come first.
        """
        # TODO: exception handling (log full details and yield ErrorStatus?)
        statuses = [
            (component, get_status()) for component, get_status in self._components.items()
        ]
        statuses.sort(key=lambda s: self._PRIORITIES[s[1].name])
        return statuses

    def highest_prefixed(self) -> ops.StatusBase:
        """Return highest-priority status with a message prefixed with the component name."""
        component, status = self.highest()
        if isinstance(status, ops.ActiveStatus) and not status.message:
            return ops.ActiveStatus()
        return ops.StatusBase.from_name(status.name, f"({component}) {status.message}")
