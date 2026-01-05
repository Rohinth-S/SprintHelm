"""
Pytest configuration and shared fixtures for CodinzHub Sprint Guardian test suite.
"""

import pytest
from pathlib import Path
from sprint_guardian.config import load_config, TeamMapConfig
from sprint_guardian.governance import ApprovalGatekeeper, AuditLogger
from sprint_guardian.jira.mock_client import MockJiraClient
from sprint_guardian.models import JiraIssue, TeamMember


@pytest.fixture
def sample_team_member():
    return TeamMember(
        name="Coder Coder",
        jira_assignee="coder.coder@codinzhub.com",
        team="CodinzHub",
        skills=["codinzhub", "lead", "automation"],
        components=["CodinzHub"],
        labels=["codinzhub", "lead"],
        max_in_progress=3,
        sprint_capacity_points=15,
        assignment_allowlist=True,
    )


@pytest.fixture
def sample_issue():
    return JiraIssue(
        key="CodinzHub-101",
        summary="Implement Model Context Protocol (MCP) server for Jira",
        status="In Progress",
        status_category="In Progress",
        priority="Highest",
        assignee="coder.coder@codinzhub.com",
        components=["CodinzHub"],
        labels=["codinzhub", "lead"],
        story_points=5,
        updated="2026-05-26T14:30:00Z",
        created="2026-05-20T10:00:00Z",
        description="Establish MCP JSON-RPC protocol endpoint exposing Jira search.",
        acceptance_criteria="MCP tools pass integration tests.",
    )


@pytest.fixture
def mock_jira():
    return MockJiraClient()


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def gatekeeper(config):
    return ApprovalGatekeeper(config)


@pytest.fixture
def audit_logger(tmp_path):
    log_file = tmp_path / "test_approvals.log"
    return AuditLogger(str(log_file))
