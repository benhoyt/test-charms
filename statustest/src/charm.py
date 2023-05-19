"""Multi-status test charm for OP033 spec.."""

import logging

import ops

logger = logging.getLogger(__name__)


class StatustestCharm(ops.CharmBase):
    def __init__(self, *args):
        super().__init__(*args)


if __name__ == "__main__":  # pragma: nocover
    ops.main(StatustestCharm)
