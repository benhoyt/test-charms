# Copyright 2022 Ben Hoyt
# See LICENSE file for licensing details.

import datetime
import unittest

import ops.testing
from ops.model import SecretNotFoundError, SecretRotate
from ops.testing import Harness

from charm import DatabaseCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        ops.testing.SIMULATE_CAN_CONNECT = True
        self.harness = Harness(DatabaseCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.set_leader()
        self.harness.begin()

    def _add_secret(self):
        # Add relation to consumer charm ("webapp") to fire _on_db_relation_created
        relation_id = self.harness.add_relation("db", "webapp")
        self.harness.add_relation_unit(relation_id, "webapp/0")

        # Get secret_id from relation data added
        relation = self.harness.model.get_relation("db", relation_id=relation_id)
        secret_id = relation.data[self.harness.model.app]["db_password_id"]

        return (secret_id, relation_id)

    def test_webapp_integration(self):
        secret_id, relation_id = self._add_secret()

        # Ensure secret content is correct
        secret = self.harness.model.get_secret(id=secret_id)
        content = secret.get_content()
        self.assertEqual(len(content), 1)
        self.assertRegex(content["password"], r"pass\d+")

        # Ensure secret metadata is correct
        info = secret.get_info()
        self.assertEqual(info.id, secret_id)
        self.assertEqual(info.label, "password")
        self.assertEqual(info.revision, 1)
        expires = datetime.datetime.now() + datetime.timedelta(hours=2)
        minute = datetime.timedelta(minutes=1)
        self.assertGreater(info.expires, expires - minute)
        self.assertLess(info.expires, expires + minute)
        self.assertEqual(info.rotation, SecretRotate.HOURLY)
        self.assertIsNotNone(info.rotates)

        # Ensure secret was granted to application
        grants = self.harness.get_secret_grants(secret_id, relation_id)
        self.assertEqual(grants, {"webapp"})

    def test_webapp_disintegration(self):
        secret_id, relation_id = self._add_secret()
        self.harness.model.get_secret(id=secret_id)

        # Remove relation to fire _on_db_relation_broken
        self.harness.remove_relation(relation_id)

        # Ensure hook removed secret
        with self.assertRaises(SecretNotFoundError):
            self.harness.model.get_secret(id=secret_id)

    def test_secret_rotate(self):
        # Add secret and fire secret-rotate hook to update secret
        secret_id, relation_id = self._add_secret()
        old_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(old_revisions), 1)

        self.harness.trigger_secret_rotation(secret_id)
        new_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(new_revisions), 2)

    def test_secret_rotate_other_label(self):
        # Add secret and fire secret-rotate hook to update secret
        secret_id, relation_id = self._add_secret()
        old_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(old_revisions), 1)

        self.harness.trigger_secret_rotation(secret_id, label="foo")
        new_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(new_revisions), 1)

    def test_secret_remove(self):
        # Add secret and create a second revision
        secret_id, relation_id = self._add_secret()
        old_revision = self.harness.get_secret_revisions(secret_id)[0]
        secret = self.harness.model.get_secret(id=secret_id)
        secret.set_content({"password": "x"})

        # Fire secret-remove hook and ensure oldest revision gets removed
        self.harness.trigger_secret_removal(secret_id, old_revision)
        new_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(new_revisions), 1)
        self.assertNotIn(old_revision, new_revisions)

    def test_secret_remove_other_label(self):
        secret_id, relation_id = self._add_secret()
        revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(revisions), 1)

        # Fire secret-remove hook with another label and ensure it's a no-op
        self.harness.trigger_secret_removal(secret_id, revisions[0], label="foo")
        self.assertEqual(self.harness.get_secret_revisions(secret_id), revisions)

    def test_secret_expired(self):
        # Add secret and create a second revision
        secret_id, relation_id = self._add_secret()
        old_revision = self.harness.get_secret_revisions(secret_id)[0]
        secret = self.harness.model.get_secret(id=secret_id)
        secret.set_content({"password": "x"})

        # Fire secret-expired hook and ensure oldest revision gets removed
        self.harness.trigger_secret_expiration(secret_id, old_revision)
        new_revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(new_revisions), 1)
        self.assertNotIn(old_revision, new_revisions)

    def test_secret_expired_other_label(self):
        secret_id, relation_id = self._add_secret()
        revisions = self.harness.get_secret_revisions(secret_id)
        self.assertEqual(len(revisions), 1)

        # Fire secret-expired hook with another label and ensure it's a no-op
        self.harness.trigger_secret_expiration(secret_id, revisions[0], label="foo")
        self.assertEqual(self.harness.get_secret_revisions(secret_id), revisions)
