"""
Human-in-the-Loop (HITL) approval gatekeeper and audit logging system.
Guarantees that no Jira mutations or assignee changes occur without verified authority sign-off.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from sprint_guardian.config import TeamMapConfig
from sprint_guardian.models import (
    ApprovalRecord,
    ConfidenceTier,
    JiraIssue,
    OperationalMode,
)


class ApprovalGatekeeper:
    """
    Enforces Human-In-The-Loop safety guardrails:
    1. Dry-run mode never mutates Jira.
    2. Report-only modes (inspect-sprint, surface-risk, progress-pulse, standup-brief, retro-notes)
       reject --apply attempts.
    3. Mutation-capable modes (shape-sprint, triage-queue, suggest-owner, balance-load)
       require verified authority in --approved-by before mutating assignees.
    4. Unapproved actions are converted to PENDING APPROVAL items with detailed reasons.
    """

    MUTATION_CAPABLE_MODES = {
        OperationalMode.SHAPE_SPRINT,
        OperationalMode.TRIAGE_QUEUE,
        OperationalMode.SUGGEST_OWNER,
        OperationalMode.BALANCE_LOAD,
    }

    def __init__(self, config: TeamMapConfig):
        self.config = config

    def can_apply_mutations(self, mode: OperationalMode, apply_flag: bool) -> bool:
        if not apply_flag:
            return False
        return mode in self.MUTATION_CAPABLE_MODES

    def verify_assignee_change(
        self,
        mode: OperationalMode,
        apply_flag: bool,
        approved_by: Optional[str],
        confidence: ConfidenceTier,
        has_hard_blocker: bool,
    ) -> bool:
        if not apply_flag:
            return False
        if not self.config.is_authorized(approved_by):
            return False
        if has_hard_blocker:
            return False
        if confidence == ConfidenceTier.LOW:
            return False
        return True

    def create_pending_approval_item(
        self,
        issue_key: str,
        current_owner: Optional[str],
        proposed_owner: str,
        confidence: ConfidenceTier,
        reason: str,
        risk: str,
    ) -> ApprovalRecord:
        return ApprovalRecord(
            issue_key=issue_key,
            previous_owner=current_owner,
            proposed_owner=proposed_owner,
            confidence=confidence,
            reason=reason,
            risk=risk,
            authority_needed="Configured Assigning Authority (e.g. Coder Coder)",
            status="PENDING APPROVAL",
            applied=False,
        )

    def create_approved_item(
        self,
        issue_key: str,
        current_owner: Optional[str],
        proposed_owner: str,
        confidence: ConfidenceTier,
        reason: str,
        approved_by: str,
        approval_note: Optional[str] = None,
    ) -> ApprovalRecord:
        return ApprovalRecord(
            issue_key=issue_key,
            previous_owner=current_owner,
            proposed_owner=proposed_owner,
            confidence=confidence,
            reason=reason,
            risk="None (Validated by assigning authority)",
            authority_needed="Approved",
            status="APPROVED",
            approved_by=approved_by,
            approval_note=approval_note,
            applied=True,
        )


class AuditLogger:
    """Records audit logs in both TSV and structured JSONL formats."""

    def __init__(self, log_path: str = "automation/output/approvals.log"):
        self.log_path = Path(log_path)
        self.jsonl_path = self.log_path.with_suffix(".jsonl")

    def log_approval(self, record: ApprovalRecord) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        # TSV append
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(record.to_tsv() + "\n")

        # JSONL append
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            entry = {
                "timestamp": record.timestamp_utc,
                "status": "applied" if record.applied else "pending",
                "issue_key": record.issue_key,
                "previous_owner": record.previous_owner,
                "proposed_owner": record.proposed_owner,
                "approved_by": record.approved_by,
                "approval_note": record.approval_note,
                "confidence": record.confidence.value,
                "reason": record.reason,
            }
            f.write(json.dumps(entry) + "\n")
