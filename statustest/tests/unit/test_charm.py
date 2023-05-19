import unittest

import ops
import ops.testing

from charm import StatustestCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = ops.testing.Harness(StatustestCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_thing(self):
        pass
