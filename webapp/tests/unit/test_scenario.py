# Copyright 2024 Ben Hoyt
# See LICENSE file for licensing details.

import scenario
from charm import WebAppCharm

"""
NOTES:
- Secrets modelling seems a bit low-level, for example having to deal with
  secret IDs and revision numbers directly, and "contents" being a dict of
  revision ID int to dict of items

- Other issues found:
  https://github.com/canonical/ops-scenario/issues/95
"""


def test_database_integration():
    # Arrange
    ctx = scenario.Context(WebAppCharm)
    relation = scenario.Relation(
        endpoint="db",
        remote_app_name="database",
        remote_app_data={"db_password_id": "SID"},
    )
    secret = scenario.Secret(
        id="SID",
        contents={0: {"password": "pass123"}},
        granted="app",
    )
    state = scenario.State(
        relations=[relation],
        secrets=[secret],
    )

    # Act
    out = ctx.run(relation.changed_event, state)

    # Assert
    assert out.secrets[0].id == "SID"
    assert out.secrets[0].label == "db_password"
    assert out.unit_status.name == "active"
    assert "would update" in out.unit_status.message


def test_db_relation_changed_no_data():
    # Arrange
    ctx = scenario.Context(WebAppCharm)
    relation = scenario.Relation(
        endpoint="db",
        remote_app_name="database",
    )
    secret = scenario.Secret(
        id="SID",
        contents={0: {"password": "pass123"}},
        granted="app",
    )
    state = scenario.State(
        relations=[relation],
        secrets=[secret],
    )

    # Act
    out = ctx.run(relation.changed_event, state)

    # Assert
    assert out.unit_status.name == "unknown"
    assert out.secrets[0].label is None


def test_secret_changed_same_content():
    # Arrange
    ctx = scenario.Context(WebAppCharm)
    secret = scenario.Secret(
        id="SID",
        contents={0: {"password": "pass123"}},
        label="db_password",
        granted="app",
    )
    state = scenario.State(
        secrets=[secret],
    )

    # Act
    out = ctx.run(secret.changed_event, state)

    # Assert
    assert out.unit_status.name == "active"
    assert "not changed" in out.unit_status.message
    assert out.secrets[0].revision == 0


def test_secret_changed_new_content():
    # Arrange
    ctx = scenario.Context(WebAppCharm)
    secret = scenario.Secret(
        id="SID",
        contents={0: {"password": "pass123"}, 1: {"password": "pass321"}},
        label="db_password",
        granted="app",
    )
    state = scenario.State(
        secrets=[secret],
    )

    # Act
    out = ctx.run(secret.changed_event, state)

    # Assert
    assert out.unit_status.name == "active"
    assert "would update" in out.unit_status.message
    assert out.secrets[0].revision == 1


def test_secret_changed_wrong_label():
    # Arrange
    ctx = scenario.Context(WebAppCharm)
    secret = scenario.Secret(
        id="SID",
        contents={},
        label="other_label",
        granted="app",
    )
    state = scenario.State(
        secrets=[secret],
    )

    # Act
    out = ctx.run(secret.changed_event, state)

    # Assert
    assert out.unit_status.name == "unknown"
