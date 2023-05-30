"""Status prioritiser."""

import typing

import ops


class Prioritiser:
    """Status prioritiser: track the highest-priority status among several components."""

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
            return ops.UnknownStatus()
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


class Group:
    """A group of components, each of which has a status.

    Each component's status is saved to stored state when its status is set,
    and is loaded when the charm is initialized.

    Args:
        app_or_unit: An Application instance to set application status (only
            valid on the leader unit), or a Unit instance to set unit status
            (valid for all units).
    """

    def __init__(self, app_or_unit: typing.Union[ops.Application, ops.Unit]):
        self._app_or_unit = app_or_unit
        self._prioritiser = Prioritiser()
        self._components = {}
        self._loaded = {}
        self._load()

    def _add(self, component: "Component") -> None:
        self._components[component.name] = component
        self._prioritiser.add(component.name, lambda: component.status)
        loaded = self._loaded.get(component.name)
        if loaded is not None:
            component._status = loaded

    def _update(self) -> None:
        self._app_or_unit.status = self._prioritiser.highest()
        self._save()

    def _load(self):
        pass  # TODO: populate self._loaded from storage

    def _save(self):
        pass  # TODO: iterate through components and save to storage


class Component:
    """A single component in a status group."""

    def __init__(self, group: Group, name: str):
        self.group = group
        self.name = name
        self._status = ops.UnknownStatus()
        self.group._add(self)

    @property
    def status(self) -> ops.StatusBase:
        """The component's status."""
        return self._status

    @status.setter
    def status(self, value: ops.StatusBase):
        """Set the component's status (and save the status group)."""
        self._status = value
        self.group._update()
