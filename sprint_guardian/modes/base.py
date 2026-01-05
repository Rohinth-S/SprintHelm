"""
Base class for all CodinzHub Sprint Guardian operational modes.
Enforces standard output order and human approval gates across workflows.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from sprint_guardian.config import TeamMapConfig
from sprint_guardian.governance import ApprovalGatekeeper, AuditLogger
from sprint_guardian.jira.client import JiraClient
from sprint_guardian.models import ApprovalRecord, OperationalMode


class BaseMode(ABC):
    def __init__(
        self,
        mode: OperationalMode,
        config: TeamMapConfig,
        jira_client: JiraClient,
        gatekeeper: ApprovalGatekeeper,
        audit_logger: AuditLogger,
        apply: bool = False,
        approved_by: Optional[str] = None,
        approval_note: Optional[str] = None,
    ):
        self.mode = mode
        self.config = config
        self.jira = jira_client
        self.gatekeeper = gatekeeper
        self.audit_logger = audit_logger
        self.apply = apply
        self.approved_by = approved_by
        self.approval_note = approval_note
        self.approval_records: List[ApprovalRecord] = []
        self.recommended_actions: List[str] = []
        self.risks: List[str] = []

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Run the operational mode and return the structured markdown response."""
        pass

    def format_output(
        self,
        summary: str,
        findings_title: str,
        findings_content: str,
    ) -> str:
        """
        Enforce standardized Output Order:
        1. Summary
        2. Findings or Proposed Scope
        3. Assignment Approval Items
        4. Recommended Jira Actions
        5. Missing Inputs or Risks
        """
        mutation_str = "apply" if self.apply else "dry-run"
        approval_str = f"approved-by {self.approved_by}" if self.approved_by else "not provided"

        lines = [
            f"# CodinzHub Sprint Guardian: {self.mode.value.replace('-', ' ').title()}",
            "",
            "## 1. Summary",
            summary,
            "",
            f"- **Execution Mode**: `{mutation_str}`",
            f"- **Assignee Approval**: `{approval_str}`",
        ]

        if self.approval_note:
            lines.append(f"- **Approval Note**: {self.approval_note}")

        lines.extend([
            "",
            f"## 2. {findings_title}",
            findings_content,
            "",
            "## 3. Assignment Approval Items",
        ])

        if not self.approval_records:
            lines.append("No pending ownership approvals required for this run.")
        else:
            for rec in self.approval_records:
                if rec.status == "APPROVED" and rec.applied:
                    lines.extend([
                        f"**APPROVED: {rec.issue_key}**",
                        f"- **Approved By**: {rec.approved_by}",
                        f"- **Applied**: Assignee changed to `{rec.proposed_owner}`",
                        f"- **Reason**: {rec.reason}",
                        "",
                    ])
                else:
                    lines.extend([
                        f"**PENDING APPROVAL: {rec.issue_key}**",
                        f"- **Current Owner**: `{rec.previous_owner or 'Unassigned'}`",
                        f"- **Proposed Owner**: `{rec.proposed_owner}`",
                        f"- **Confidence**: `{rec.confidence.value}`",
                        f"- **Reason**: {rec.reason}",
                        f"- **Risk**: {rec.risk}",
                        f"- **Authority Needed**: {rec.authority_needed}",
                        "",
                    ])

        lines.extend([
            "## 4. Recommended Jira Actions",
        ])

        if not self.recommended_actions:
            lines.append("No further Jira mutations recommended at this time.")
        else:
            for action in self.recommended_actions:
                lines.append(f"- {action}")

        lines.extend([
            "",
            "## 5. Missing Inputs or Risks",
        ])

        if not self.risks:
            lines.append("No critical missing inputs or policy blockers detected.")
        else:
            for r in self.risks:
                lines.append(f"- ⚠️ {r}")

        return "\n".join(lines)
