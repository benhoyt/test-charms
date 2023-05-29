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
        """Add a named status component. Components added first have higher priority."""
        if component in self._components:
            raise ValueError(f"duplicate component {component!r}")
        self._components[component] = get_status

    def highest(self) -> ops.StatusBase:
        """Return highest-priority status with a message prefixed with the component name."""
        status, component = self.highest_with_name()
        if isinstance(status, ops.ActiveStatus) and not status.message:
            return ops.ActiveStatus()
        return ops.StatusBase.from_name(status.name, f"[{component}] {status.message}")

    def highest_with_name(self) -> typing.Tuple[ops.StatusBase, str]:
        """Return tuple of raw, highest-priority status and component name."""
        if not self._components:
            return (ops.ActiveStatus(), "")
        # TODO: exception handling (log full details and yield ErrorStatus?)
        statuses = [
            (get_status(), component) for component, get_status in self._components.items()
        ]
        statuses.sort(key=lambda s: self._PRIORITIES[s[0].name])
        return statuses[0]

    def highest_prefixed(self) -> ops.StatusBase:
        """Return highest-priority status with a message prefixed with the component name."""
        component, status = self.highest()
        if isinstance(status, ops.ActiveStatus) and not status.message:
            return ops.ActiveStatus()
        return ops.StatusBase.from_name(status.name, f"({component}) {status.message}")
