"""
Mode: codinzhub-surface-risk
Surfaces delivery threats before they become sprint blockers:
critical paths, single-point-of-failure risks, stale items, and developer overload.
"""

from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue
from sprint_guardian.modes.base import BaseMode


class SurfaceRiskMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.SURFACE_RISK, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND statusCategory != Done AND (assignee is EMPTY OR updated <= -3d OR status in ('Blocked', 'On Hold', 'In Review', 'Testing')) ORDER BY priority DESC"
        risky_issues = self.jira.query_issues(query)
        team = self.config.get_all_members()

        findings_lines = [
            "### Delivery Risk Radar & Impact Matrix",
            "",
            "| Risk Tier | Issue Key | Impact Description | Probable Cause | Owner / Action Owner | Recommended Mitigation |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        critical_count = 0
        moderate_count = 0

        for issue in risky_issues:
            if issue.is_blocked:
                critical_count += 1
                findings_lines.append(
                    f"| 🔴 **CRITICAL** | `{issue.key}` | Blocks sprint goal delivery | Upstream blocker ({', '.join(issue.blocked_by) or 'Dependency'}) | `{issue.assignee or 'Unassigned'}` | Swarm technical dependency immediately |"
                )
                self.risks.append(f"CRITICAL: {issue.key} is blocking downstream deliverables.")
            elif not issue.assignee and issue.priority.lower() in ("highest", "high"):
                critical_count += 1
                findings_lines.append(
                    f"| 🔴 **CRITICAL** | `{issue.key}` | High-priority work unstaffed | Backlog queue lag / no owner assigned | `Team Lead` | Run `codinzhub-suggest-owner` and assign |"
                )
                self.risks.append(f"CRITICAL: {issue.key} has priority {issue.priority} but no assignee.")
            elif issue.status.lower() in ("in review", "testing"):
                moderate_count += 1
                findings_lines.append(
                    f"| 🟡 **MODERATE** | `{issue.key}` | Review queue bottleneck | Testing/Review capacity constraints | `{issue.assignee or 'Unassigned'}` | Allocate dedicated peer reviewer today |"
                )
            else:
                moderate_count += 1
                findings_lines.append(
                    f"| 🟡 **MODERATE** | `{issue.key}` | Potential sprint rollover | Stale inactivity for >3 days | `{issue.assignee or 'Unassigned'}` | Check in during standup for hidden impediments |"
                )

        summary = (
            f"Delivery Risk Radar detected **{critical_count} critical delivery threat(s)** and **{moderate_count} moderate risk(s)** "
            f"across active project scope. Primary impediments: blocker dependencies, unstaffed critical path tickets, and stale items."
        )

        self.recommended_actions.append("Convene emergency triage for all critical delivery threats before end-of-day.")
        self.recommended_actions.append("Reallocate code review capacity to clear testing bottlenecks.")

        return self.format_output(summary, "Delivery Risks", "\n".join(findings_lines))
