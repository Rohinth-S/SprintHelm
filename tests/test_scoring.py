"""
Unit tests for OwnershipScorer and ReadinessScorer.
"""

from sprint_guardian.models import ConfidenceTier, JiraIssue, TeamMember
from sprint_guardian.scoring import OwnershipScorer, ReadinessScorer


def test_ownership_scoring_positive_signals(sample_issue, sample_team_member):
    sb = OwnershipScorer.score_candidate(
        issue=sample_issue,
        candidate=sample_team_member,
        active_issues_for_candidate=[],
        is_backup=True,
        recent_activity=True,
    )
    # +4 component, +3 label, +3 skill, +2 recent activity, +1 backup = +13
    assert sb.total_score >= 10
    assert sb.confidence == ConfidenceTier.HIGH
    assert sb.has_hard_blocker is False


def test_ownership_scoring_wip_exceeded(sample_issue, sample_team_member):
    # Member max WIP is 3. Pass 3 active issues.
    active_issues = [
        JiraIssue(key=f"TEST-{i}", summary="Task", status="In Progress")
        for i in range(sample_team_member.max_in_progress)
    ]
    sb = OwnershipScorer.score_candidate(
        issue=sample_issue,
        candidate=sample_team_member,
        active_issues_for_candidate=active_issues,
    )
    assert sb.is_wip_exceeded is True
    assert sb.has_hard_blocker is True
    assert sb.confidence == ConfidenceTier.LOW


def test_ownership_scoring_disallowlist(sample_issue, sample_team_member):
    sample_team_member.assignment_allowlist = False
    sb = OwnershipScorer.score_candidate(
        issue=sample_issue,
        candidate=sample_team_member,
        active_issues_for_candidate=[],
    )
    assert sb.has_hard_blocker is True
    assert sb.confidence == ConfidenceTier.LOW


def test_readiness_scoring(sample_issue):
    rb = ReadinessScorer.score_readiness(sample_issue, has_safe_owner=True)
    assert rb.is_ready is True
    assert rb.total_score >= 5

    # Blocked issue must never be ready
    sample_issue.status = "Blocked"
    sample_issue.blocked_by = ["DEP-1"]
    rb_blocked = ReadinessScorer.score_readiness(sample_issue, has_safe_owner=True)
    assert rb_blocked.is_ready is False
