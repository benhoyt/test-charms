"""Status prioritizer."""

import typing

import ops

# TODO: could have StatusPrioritizer automatically observe commit and set app or unit status,
#       but then it needs to know about the framework and charm


class StatusPrioritizer:
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

    def highest(self) -> typing.Tuple[str, ops.StatusBase]:
        """Return highest-priority status as tuple of component name and status."""
        if not self._components:
            return ("", ops.ActiveStatus())
        # TODO: exception handling (log full details and yield ErrorStatus)
        statuses = [
            (component, get_status()) for component, get_status in self._components.items()
        ]
        statuses.sort(key=lambda s: self._PRIORITIES[s[1].name])
        return statuses[0]

    def highest_prefixed(self) -> ops.StatusBase:
        """Return highest-priority status with a message prefixed with the component name."""
        component, status = self.highest()
        if isinstance(status, ops.ActiveStatus) and not status.message:
            return ops.ActiveStatus()
        return ops.StatusBase.from_name(status.name, f"({component}) {status.message}")
