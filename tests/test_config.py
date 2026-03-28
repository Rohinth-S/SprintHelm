"""
Unit tests for configuration loading and authority verification.
"""

from sprint_guardian.config import load_config, TeamMapConfig


def test_config_loads_default_values(config):
    assert config.board_id is not None
    assert "CodinzHub" in config.project_keys
    assert config.assignee_change_requires_approval is True


def test_is_authorized(config):
    assert config.is_authorized("Rohinth S") is True
    assert config.is_authorized("imt_2024068@iiitm.ac.in") is True
    assert config.is_authorized("Unknown Person") is False
    assert config.is_authorized("") is False
    assert config.is_authorized(None) is False


def test_get_member(config):
    member = config.get_member("imt_2024068@iiitm.ac.in")
    assert member is not None
    assert member.name == "Rohinth S"
    assert member.max_in_progress >= 1
