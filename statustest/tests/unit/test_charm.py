import unittest

import ops
import ops.testing
from charm import StatustestCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = ops.testing.Harness(StatustestCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_initial(self):
        status = self.harness.model.unit.status
        self.assertEqual(status.name, "blocked")
        self.assertEqual(status.message, '[database] "database_mode" required')

    def test_database_mode_set(self):
        self.harness.update_config({"database_mode": "single"})
        status = self.harness.model.unit.status
        self.assertEqual(status.name, "blocked")
        self.assertEqual(status.message, '[webapp] "webapp_port" required')

    def test_webapp_port_set(self):
        self.harness.update_config({"webapp_port": 8080})
        status = self.harness.model.unit.status
        self.assertEqual(status.name, "blocked")
        self.assertEqual(status.message, '[database] "database_mode" required')

    def test_all_config_set(self):
        self.harness.update_config({"database_mode": "single", "webapp_port": 8080})
        status = self.harness.model.unit.status
        self.assertEqual(status.name, "active")
