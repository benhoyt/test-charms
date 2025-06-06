import pytest
from ops import testing

import charm


def test_debug_action_default():
    ctx = testing.Context(charm.DatabaseCharm)
    ctx.run(ctx.on.action("debug"), testing.State())
    assert ctx.action_results == {"params": {}}


def test_debug_action_exception():
    ctx = testing.Context(charm.DatabaseCharm)
    with pytest.raises(testing.errors.UncaughtCharmError):
        ctx.run(ctx.on.action("debug", {"mode": "exc"}), testing.State())
