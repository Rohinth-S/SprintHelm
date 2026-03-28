"""
Unit tests for domain models and data entities.
"""

from sprint_guardian.models import (
    ApprovalRecord,
    ConfidenceTier,
    JiraIssue,
    OperationalMode,
    TeamMember,
)


def test_jira_issue_status_flags(sample_issue):
    assert sample_issue.is_in_progress is True
    assert sample_issue.is_done is False
    assert sample_issue.is_blocked is False

    done_issue = JiraIssue(key="TEST-1", summary="Done test", status="Done", status_category="Done")
    assert done_issue.is_done is True

    blocked_issue = JiraIssue(key="TEST-2", summary="Blocked test", status="Blocked", blocked_by=["TEST-1"])
    assert blocked_issue.is_blocked is True


def test_team_member_matching(sample_team_member):
    assert sample_team_member.matches_skill("automation") is True
    assert sample_team_member.matches_skill("non-existent") is False
    assert sample_team_member.matches_component("CodinzHub") is True
    assert sample_team_member.matches_label("lead") is True


def test_approval_record_tsv_serialization():
    rec = ApprovalRecord(
        issue_key="CodinzHub-101",
        previous_owner="old@example.com",
        proposed_owner="new@example.com",
        confidence=ConfidenceTier.HIGH,
        reason="Skill match",
        risk="None",
        authority_needed="Lead",
        status="APPROVED",
        approved_by="Rohinth S",
        applied=True,
    )
    tsv = rec.to_tsv()
    assert "status=completed" in tsv
    assert "approved_by=Rohinth S" in tsv
    assert "issue_keys=CodinzHub-101" in tsv
    assert "target=new@example.com" in tsv
