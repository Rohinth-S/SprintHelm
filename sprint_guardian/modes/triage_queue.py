"""
Mode: codinzhub-triage-queue
Classifies incoming backlog work and identifies next actions.
"""

from typing import Dict, List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue, TriageCategory
from sprint_guardian.modes.base import BaseMode


class TriageQueueMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.TRIAGE_QUEUE, **kwargs)

    def execute(self, jql: Optional[str] = None, **kwargs) -> str:
        query = jql or self.config.backlog_jql or f"project in ({','.join(self.config.project_keys)}) AND statusCategory != Done AND sprint is EMPTY ORDER BY priority DESC, updated ASC"
        issues = self.jira.query_issues(query)

        classified: Dict[TriageCategory, List[JiraIssue]] = {
            TriageCategory.READY: [],
            TriageCategory.SPRINT_CANDIDATE: [],
            TriageCategory.OWNER_NEEDED: [],
            TriageCategory.NEEDS_INFO: [],
            TriageCategory.BLOCKED: [],
            TriageCategory.DUPLICATE: [],
        }

        for issue in issues:
            if issue.is_blocked:
                classified[TriageCategory.BLOCKED].append(issue)
            elif not issue.description or len(issue.description.strip()) < 25 or not issue.acceptance_criteria:
                classified[TriageCategory.NEEDS_INFO].append(issue)
            elif not issue.assignee:
                classified[TriageCategory.OWNER_NEEDED].append(issue)
            elif issue.priority.lower() in ("highest", "high") and issue.story_points > 0:
                classified[TriageCategory.SPRINT_CANDIDATE].append(issue)
            else:
                classified[TriageCategory.READY].append(issue)

        total_triaged = len(issues)
        summary = (
            f"Triaged **{total_triaged} queue issues** across CodinzHub backlog. "
            f"Found **{len(classified[TriageCategory.SPRINT_CANDIDATE])} sprint candidates**, "
            f"**{len(classified[TriageCategory.OWNER_NEEDED])} unassigned items**, "
            f"**{len(classified[TriageCategory.NEEDS_INFO])} items missing acceptance criteria**, and "
            f"**{len(classified[TriageCategory.BLOCKED])} blocked issues**."
        )

        lines = [
            "### Queue Classification Breakdown",
            "",
            "| Category | Count | Primary Next Action |",
            "| :--- | :--- | :--- |",
            f"| **Sprint Candidates** | {len(classified[TriageCategory.SPRINT_CANDIDATE])} | Scope into upcoming sprint planning |",
            f"| **Ready for Grooming** | {len(classified[TriageCategory.READY])} | Review during backlog refinement |",
            f"| **Owner Needed** | {len(classified[TriageCategory.OWNER_NEEDED])} | Run `codinzhub-suggest-owner` |",
            f"| **Needs Information** | {len(classified[TriageCategory.NEEDS_INFO])} | Request product/QA acceptance criteria |",
            f"| **Blocked** | {len(classified[TriageCategory.BLOCKED])} | Triage blocker dependencies |",
            "",
            "### Detailed Queue Findings",
            "",
            "| Issue Key | Summary | Priority | Category | Next Step |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for cat, items in classified.items():
            for item in items:
                next_step = {
                    TriageCategory.SPRINT_CANDIDATE: "Schedule into next sprint",
                    TriageCategory.READY: "Ready for team pickup",
                    TriageCategory.OWNER_NEEDED: "Assign engineer",
                    TriageCategory.NEEDS_INFO: "Define acceptance criteria",
                    TriageCategory.BLOCKED: f"Clear blocker: {', '.join(item.blocked_by) or 'Dependencies'}",
                    TriageCategory.DUPLICATE: "Link related issue",
                }[cat]
                lines.append(f"| `{item.key}` | {item.summary} | **{item.priority}** | `{cat.value}` | {next_step} |")

        for item in classified[TriageCategory.NEEDS_INFO]:
            self.risks.append(f"{item.key} is missing explicit acceptance criteria.")

        for item in classified[TriageCategory.BLOCKED]:
            self.risks.append(f"{item.key} is marked blocked ({', '.join(item.blocked_by) or 'Dependency'}).")

        self.recommended_actions.append("Prioritize refining items under 'Needs Information' with product management.")
        self.recommended_actions.append("Run `codinzhub-suggest-owner` for all items under 'Owner Needed'.")

        return self.format_output(summary, "Backlog Queue Classification", "\n".join(lines))
