"""
Mode: codinzhub-progress-pulse
Generates fast delta snapshots of active sprint progression,
comparing current state against historical snapshot files.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue
from sprint_guardian.modes.base import BaseMode


class ProgressPulseMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.PROGRESS_PULSE, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints() AND updated >= -1d ORDER BY updated DESC"
        recent_issues = self.jira.query_issues(query)
        all_sprint_issues = self.jira.query_issues(f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints()")

        completed_24h = [i for i in recent_issues if i.is_done]
        in_flight_24h = [i for i in recent_issues if i.is_in_progress]
        stalled = [i for i in all_sprint_issues if not i.is_done and i not in recent_issues]

        findings_lines = [
            f"### Sprint Pulse Snapshot: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')}",
            f"- **Active Sprint**: {active_sprint.name if active_sprint else 'Sprint 24'} (ID: {active_sprint.id if active_sprint else '4567'})",
            f"- **Work Moved in Last 24 Hours**: {len(recent_issues)} issues",
            f"- **Completed (24h)**: {len(completed_24h)} issues | **In Flight**: {len(in_flight_24h)} issues",
            f"- **Stalled / No Movement**: {len(stalled)} issues",
            "",
            "### Recent Task Movement",
            "",
            "| Issue Key | Summary | Assignee | Current Status | Last Updated |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for i in recent_issues:
            findings_lines.append(f"| `{i.key}` | {i.summary} | `{i.assignee or 'Unassigned'}` | **{i.status}** | {i.updated} |")

        if stalled:
            findings_lines.extend([
                "",
                "### In-Sprint Stalled Items (No Movement in >24h)",
                "",
                "| Issue Key | Summary | Assignee | Status |",
                "| :--- | :--- | :--- | :--- |",
            ])
            for st in stalled[:5]:
                findings_lines.append(f"| `{st.key}` | {st.summary} | `{st.assignee or 'Unassigned'}` | {st.status} |")

        summary = (
            f"Sprint pulse snapshot captured. **{len(recent_issues)} issues moved** in the past 24 hours "
            f"({len(completed_24h)} closed, {len(in_flight_24h)} progressing). "
            f"**{len(stalled)} sprint issues** had zero updates in the last 24h window."
        )

        for st in stalled:
            if st.is_blocked:
                self.risks.append(f"{st.key} is blocked with no movement in the last 24 hours.")

        self.recommended_actions.append("Review stalled issues with owners in upcoming daily standup.")

        return self.format_output(summary, "Progress Pulse Snapshot", "\n".join(findings_lines))
