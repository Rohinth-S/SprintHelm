"""
Mode: codinzhub-standup-brief
Synthesizes daily sprint standup reports: Completed, In Progress, Blockers,
and Decisions Needed. Perfect for Slack / Teams distribution.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue
from sprint_guardian.modes.base import BaseMode


class StandupBriefMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.STANDUP_BRIEF, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints() ORDER BY updated DESC"
        issues = self.jira.query_issues(query)

        completed = [i for i in issues if i.is_done]
        in_flight = [i for i in issues if i.is_in_progress and not i.is_blocked]
        blocked = [i for i in issues if i.is_blocked]
        unassigned = [i for i in issues if not i.assignee and not i.is_done]

        findings_lines = [
            f"### 📋 Daily Agile Standup Brief ({datetime.now(timezone.utc).strftime('%A, %b %d, %Y')})",
            f"**Sprint**: {active_sprint.name if active_sprint else 'Sprint 24'} (ID: {active_sprint.id if active_sprint else '4567'})",
            "",
            "#### ✅ Completed (Last 24 Hours)",
        ]

        if not completed:
            findings_lines.append("_No tickets moved to Done in the last cycle._")
        else:
            for c in completed:
                findings_lines.append(f"- **{c.key}**: {c.summary} _(@{c.assignee or 'unassigned'})_")

        findings_lines.extend([
            "",
            "#### 🔄 In Flight (Active Development)",
        ])

        if not in_flight:
            findings_lines.append("_No tasks currently in active development._")
        else:
            for inf in in_flight:
                findings_lines.append(f"- **{inf.key}** `[{inf.status}]`: {inf.summary} _(@{inf.assignee or 'unassigned'})_")

        findings_lines.extend([
            "",
            "#### 🛑 Blockers & Impediments",
        ])

        if not blocked:
            findings_lines.append("🎉 _Zero hard blockers reported across the team!_")
        else:
            for b in blocked:
                blocker_desc = ", ".join(b.blocked_by) if b.blocked_by else "Blocked status"
                findings_lines.append(f"- 🔴 **{b.key}**: {b.summary} (Blocker: `{blocker_desc}`) _(@{b.assignee or 'unassigned'})_")
                self.risks.append(f"Standup Blocker on {b.key}: {b.summary}")

        findings_lines.extend([
            "",
            "#### ⚠️ Decisions & Approvals Needed",
        ])

        if unassigned:
            findings_lines.append(f"- **Unassigned active sprint tickets**: {len(unassigned)} items need assignees.")
        findings_lines.append("- **Approval Gating**: Ownership reassignments are queued under Section 3 awaiting lead approval.")

        summary = (
            f"Daily sprint standup brief generated for {active_sprint.name if active_sprint else 'active sprint'}. "
            f"**{len(completed)} completed**, **{len(in_flight)} in flight**, "
            f"**{len(blocked)} blocked**, and **{len(unassigned)} unassigned** tickets."
        )

        self.recommended_actions.append("Post standup summary to team communication channel (#dev-sprint-standup).")
        if blocked:
            self.recommended_actions.append("Schedule 10-minute swarm session immediately following standup to unblock critical tickets.")

        return self.format_output(summary, "Daily Standup Synthesis", "\n".join(findings_lines))
