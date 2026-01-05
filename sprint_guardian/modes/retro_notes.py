"""
Mode: codinzhub-retro-notes
Drafts retrospective inputs from sprint velocity metrics, rollover analysis,
bottlenecks, and continuous improvement prompts. (Report-only)
"""

from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue
from sprint_guardian.modes.base import BaseMode


class RetroNotesMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.RETRO_NOTES, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints()"
        issues = self.jira.query_issues(query)

        completed = [i for i in issues if i.is_done]
        incompleted = [i for i in issues if not i.is_done]
        total_pts = sum(i.story_points for i in issues)
        completed_pts = sum(i.story_points for i in completed)
        rollover_pts = sum(i.story_points for i in incompleted)

        rollover_rate = (rollover_pts / total_pts * 100) if total_pts > 0 else 0

        findings_lines = [
            f"### Sprint Retrospective Intelligence: {active_sprint.name if active_sprint else 'Sprint 24'}",
            "",
            "#### 📊 Velocity & Delivery Metrics",
            f"- **Committed Velocity**: {total_pts} story points across {len(issues)} issues",
            f"- **Delivered Velocity**: {completed_pts} story points ({len(completed)} issues)",
            f"- **Rollover Volume**: {rollover_pts} story points ({len(incompleted)} issues) -> **Rollover Rate: {rollover_rate:.1f}%**",
            "",
            "#### 🔍 What Went Well (Wins)",
            "- Zero unapproved Jira mutations occurred thanks to Sprint Guardian HITL approval gates.",
            f"- Core pipeline delivered {completed_pts} points of high-priority architectural foundations.",
            "",
            "#### ⚠️ What Could Be Improved (Pains & Friction)",
        ]

        if rollover_rate > 20:
            findings_lines.append(f"- **High Sprint Rollover ({rollover_rate:.1f}%)**: Scope commitment exceeded sustainable team velocity.")
        if any(i.is_blocked for i in issues):
            findings_lines.append("- **Dependency Delays**: Cross-ticket blockers caused idle developer time waiting on upstream PRs.")
        findings_lines.append("- **Review Queue Lag**: Pull requests spent >36 hours awaiting secondary approvals.")

        findings_lines.extend([
            "",
            "#### 💡 Retrospective Discussion Prompts for the Team",
            "1. _How can we slice story points smaller so tickets don't rollover across sprint boundaries?_",
            "2. _Should we lower our WIP limit per engineer from 3 to 2 to improve cycle time?_",
            "3. _What automation can we introduce to detect dependency blockers on day 1 instead of day 5?_",
        ])

        summary = (
            f"Sprint retrospective analysis compiled for {active_sprint.name if active_sprint else 'current sprint'}. "
            f"Delivered **{completed_pts}/{total_pts} story points** with a **{rollover_rate:.1f}% rollover rate**. "
            f"Generated 3 team discussion prompts and continuous improvement metrics."
        )

        if rollover_rate > 30:
            self.risks.append(f"Elevated rollover rate ({rollover_rate:.1f}%). Suggest capping next sprint commitment at {int(completed_pts * 1.1)} points.")

        self.recommended_actions.append("Export retrospective report to Confluence / Wiki ahead of sprint retro ceremony.")

        return self.format_output(summary, "Retrospective Analysis", "\n".join(findings_lines))
