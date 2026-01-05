"""
Unit tests for Human-in-the-Loop (HITL) ApprovalGatekeeper and AuditLogger.
"""

from sprint_guardian.models import ConfidenceTier, OperationalMode


def test_gatekeeper_dry_run_never_mutates(gatekeeper):
    can_apply = gatekeeper.can_apply_mutations(OperationalMode.SUGGEST_OWNER, apply_flag=False)
    assert can_apply is False


def test_gatekeeper_report_only_modes_reject_apply(gatekeeper):
    assert gatekeeper.can_apply_mutations(OperationalMode.INSPECT_SPRINT, apply_flag=True) is False
    assert gatekeeper.can_apply_mutations(OperationalMode.STANDUP_BRIEF, apply_flag=True) is False
    assert gatekeeper.can_apply_mutations(OperationalMode.RETRO_NOTES, apply_flag=True) is False


def test_gatekeeper_verified_assignee_change(gatekeeper):
    # Authorized lead with high confidence
    verified = gatekeeper.verify_assignee_change(
        mode=OperationalMode.SUGGEST_OWNER,
        apply_flag=True,
        approved_by="Coder Coder",
        confidence=ConfidenceTier.HIGH,
        has_hard_blocker=False,
    )
    assert verified is True

    # Unauthorized person
    unauthorized = gatekeeper.verify_assignee_change(
        mode=OperationalMode.SUGGEST_OWNER,
        apply_flag=True,
        approved_by="Random Hacker",
        confidence=ConfidenceTier.HIGH,
        has_hard_blocker=False,
    )
    assert unauthorized is False

    # Low confidence cannot auto-apply
    low_conf = gatekeeper.verify_assignee_change(
        mode=OperationalMode.SUGGEST_OWNER,
        apply_flag=True,
        approved_by="Coder Coder",
        confidence=ConfidenceTier.LOW,
        has_hard_blocker=False,
    )
    assert low_conf is False


def test_audit_logger_records_entries(audit_logger, gatekeeper):
    rec = gatekeeper.create_approved_item(
        issue_key="CodinzHub-108",
        current_owner=None,
        proposed_owner="engineer.one@example.com",
        confidence=ConfidenceTier.HIGH,
        reason="Test approval",
        approved_by="Coder Coder",
    )
    audit_logger.log_approval(rec)

    assert audit_logger.log_path.exists()
    content = audit_logger.log_path.read_text(encoding="utf-8")
    assert "status=completed" in content
    assert "approved_by=Coder Coder" in content
