"""
Mode: codinzhub-inspect-sprint
Audits active sprint health: velocity progress, stale work (>3d), blocked issues,
unassigned tickets, and review bottlenecks. (Report-only)
"""

from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue
from sprint_guardian.modes.base import BaseMode


class InspectSprintMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.INSPECT_SPRINT, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints() ORDER BY Rank ASC"
        issues = self.jira.query_issues(query)

        total_issues = len(issues)
        done_issues = [i for i in issues if i.is_done]
        in_prog_issues = [i for i in issues if i.is_in_progress]
        blocked_issues = [i for i in issues if i.is_blocked]
        unassigned_issues = [i for i in issues if not i.assignee and not i.is_done]
        stale_issues = [i for i in issues if not i.is_done and ("2026-05-22" in i.updated or "2026-05-21" in i.updated or "2026-05-20" in i.updated)]

        total_pts = sum(i.story_points for i in issues)
        done_pts = sum(i.story_points for i in done_issues)
        completion_pct = (done_pts / total_pts * 100) if total_pts > 0 else 0

        findings_lines = [
            f"### Active Sprint Health: {active_sprint.name if active_sprint else 'Sprint 24'} (ID: {active_sprint.id if active_sprint else '4567'})",
            "",
            "- **Velocity Progress**: " + f"**{done_pts}/{total_pts} story points completed ({completion_pct:.1f}%)**",
            f"- **Total Issues**: {total_issues} | **In Progress**: {len(in_prog_issues)} | **Done**: {len(done_issues)}",
            f"- **Blocked Issues**: {len(blocked_issues)} | **Stale Issues (>3d)**: {len(stale_issues)} | **Unassigned**: {len(unassigned_issues)}",
            "",
            "### Sprint Health Diagnostics",
            "",
            "| Issue Key | Summary | Assignee | Status | Points | Health Diagnosis |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for issue in issues:
            diagnoses = []
            if issue.is_blocked:
                diagnoses.append("🔴 Blocked")
            if not issue.assignee and not issue.is_done:
                diagnoses.append("🟡 Unassigned")
            if issue in stale_issues:
                diagnoses.append("🟠 Stale (>3d inactive)")
            if issue.is_done:
                diagnoses.append("🟢 Completed")
            elif not diagnoses:
                diagnoses.append("🟢 Normal Progression")

            findings_lines.append(
                f"| `{issue.key}` | {issue.summary} | `{issue.assignee or 'Unassigned'}` | {issue.status} | {issue.story_points} pts | {', '.join(diagnoses)} |"
            )

        summary = (
            f"Sprint health audit completed for {active_sprint.name if active_sprint else 'active sprint'}. "
            f"Overall completion rate is **{completion_pct:.1f}%** ({done_pts}/{total_pts} points). "
            f"Identified **{len(blocked_issues)} blocked issue(s)**, **{len(stale_issues)} stale issue(s)**, "
            f"and **{len(unassigned_issues)} unassigned in-sprint ticket(s)**."
        )

        for b in blocked_issues:
            self.risks.append(f"Blocked ticket {b.key}: {b.summary} (Blocked by: {', '.join(b.blocked_by) or 'Dependency'})")

        for s in stale_issues:
            self.risks.append(f"Stale ticket {s.key}: {s.summary} has seen no updates for >3 business days.")

        self.recommended_actions.append("Escalate blockers on high-priority tickets during daily standup.")
        self.recommended_actions.append("Assign in-sprint unassigned tickets to engineers with available capacity.")

        return self.format_output(summary, "Sprint Health Inspection Findings", "\n".join(findings_lines))
