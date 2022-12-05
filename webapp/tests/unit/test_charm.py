# Copyright 2022 Ben Hoyt
# See LICENSE file for licensing details.

import unittest

import ops.testing
from ops.testing import Harness

from charm import WebAppCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.harness = Harness(WebAppCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def _add_secret(self):
        relation_id = self.harness.add_relation("db", "database")
        self.harness.add_relation_unit(relation_id, "database/0")
        secret_id = self.harness.add_secret("database", {"password": "pass123"})
        self.harness.grant_secret(secret_id, "webapp")
        return (secret_id, relation_id)

    def test_database_integration(self):
        # Add secret and grant this charm access
        secret_id, relation_id = self._add_secret()

        # Update relation data to fire _on_db_relation_changed
        self.harness.update_relation_data(relation_id, "database", {"db_password_id": secret_id})

        # Ensure secret's consumer label was updated
        secret = self.harness.model.get_secret(label="db_password")
        self.assertEqual(secret.label, "db_password")
        self.assertEqual(secret.get_content(), {"password": "pass123"})

    def test_secret_changed(self):
        # Add secret and grant this charm access
        secret_id, relation_id = self._add_secret()

        # Update relation data to fire _on_db_relation_changed
        self.harness.update_relation_data(relation_id, "database", {"db_password_id": secret_id})

        # Set secret content to fire _on_secret_changed (without actually changing it)
        self.harness.set_secret_content(secret_id, {"password": "pass123"})
        secret = self.harness.model.get_secret(id=secret_id)
        self.assertEqual(secret.get_content(), {"password": "pass123"})

        # Set secret content to fire _on_secret_changed (with real changes)
        self.harness.set_secret_content(secret_id, {"password": "pass321"})
        secret = self.harness.model.get_secret(id=secret_id)
        self.assertEqual(secret.get_content(), {"password": "pass321"})
