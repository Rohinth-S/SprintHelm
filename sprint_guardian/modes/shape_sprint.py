"""
Mode: codinzhub-shape-sprint
Shapes sprint scope from backlog or board issues adhering to capacity points and readiness.
"""

from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue, ConfidenceTier
from sprint_guardian.modes.base import BaseMode
from sprint_guardian.scoring import ReadinessScorer, OwnershipScorer


class ShapeSprintMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.SHAPE_SPRINT, **kwargs)

    def execute(
        self,
        board_id: Optional[str] = None,
        sprint_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        jql: Optional[str] = None,
        **kwargs,
    ) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = jql or self.config.backlog_jql or f"project in ({','.join(self.config.project_keys)}) AND statusCategory != Done AND sprint is EMPTY ORDER BY priority DESC, created ASC"

        backlog_issues = self.jira.query_issues(query)
        team_members = self.config.get_all_members()
        total_team_capacity = sum(m.sprint_capacity_points for m in team_members)

        selected: List[JiraIssue] = []
        deferred: List[JiraIssue] = []
        risky: List[JiraIssue] = []
        committed_points = 0

        for issue in backlog_issues:
            # Score readiness
            has_owner = bool(issue.assignee)
            readiness = ReadinessScorer.score_readiness(issue, has_safe_owner=has_owner)

            if issue.is_blocked:
                risky.append(issue)
                self.risks.append(f"{issue.key} is blocked ({', '.join(issue.blocked_by) or 'Status: Blocked'}). Excluded from scope.")
                continue

            if not has_owner:
                # Evaluate if a candidate owner exists
                best_cand = None
                best_score = -10
                for cand in team_members:
                    active_cand = [i for i in backlog_issues if i.assignee == cand.jira_assignee and i.is_in_progress]
                    sb = OwnershipScorer.score_candidate(issue, cand, active_cand)
                    if sb.total_score > best_score:
                        best_score = sb.total_score
                        best_cand = (cand, sb)

                if best_cand and best_cand[1].confidence != ConfidenceTier.LOW:
                    cand_obj, sb = best_cand
                    if self.apply and self.gatekeeper.verify_assignee_change(self.mode, self.apply, self.approved_by, sb.confidence, sb.has_hard_blocker):
                        self.jira.assign_issue(issue.key, cand_obj.jira_assignee)
                        self.approval_records.append(
                            self.gatekeeper.create_approved_item(
                                issue.key, None, cand_obj.jira_assignee, sb.confidence,
                                f"Sprint shaping assignment: {', '.join(sb.positive_signals)}", self.approved_by, self.approval_note
                            )
                        )
                    else:
                        self.approval_records.append(
                            self.gatekeeper.create_pending_approval_item(
                                issue.key, None, cand_obj.jira_assignee, sb.confidence,
                                f"Sprint shaping proposed assignment: {', '.join(sb.positive_signals)}",
                                "Assignee change pending approval before sprint commitment"
                            )
                        )
                else:
                    deferred.append(issue)
                    self.risks.append(f"{issue.key} has no safe owner. Deferred to next refinement.")
                    continue

            pts = issue.story_points or 3
            if committed_points + pts <= total_team_capacity:
                selected.append(issue)
                committed_points += pts
            else:
                deferred.append(issue)

        # Build output sections
        summary = (
            f"Evaluated {len(backlog_issues)} backlog candidate tickets for sprint scoping. "
            f"Proposed commitment of **{len(selected)} issues** totaling **{committed_points} story points** "
            f"(Team capacity: {total_team_capacity} pts across {len(team_members)} engineers). "
            f"Deferred {len(deferred)} tickets and flagged {len(risky)} delivery risks."
        )

        findings_lines = [
            f"### Proposed Sprint Commitment: {sprint_name or 'Upcoming Sprint'} ({committed_points}/{total_team_capacity} pts)",
            "",
            "| Issue Key | Summary | Priority | Assignee | Points | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for s in selected:
            findings_lines.append(f"| `{s.key}` | {s.summary} | **{s.priority}** | `{s.assignee or 'Pending'}` | {s.story_points or 3} pts | {s.status} |")

        if deferred:
            findings_lines.extend([
                "",
                "### Deferred Backlog Candidates",
                "",
                "| Issue Key | Summary | Reason |",
                "| :--- | :--- | :--- |",
            ])
            for d in deferred:
                reason = "Exceeds remaining sprint capacity" if (committed_points + (d.story_points or 3)) > total_team_capacity else "Missing owner / refinement"
                findings_lines.append(f"| `{d.key}` | {d.summary} | {reason} |")

        findings_content = "\n".join(findings_lines)

        if self.apply:
            self.recommended_actions.append(f"Attach {len(selected)} selected issues to sprint scope in Jira.")
        else:
            self.recommended_actions.append(f"Run with `--apply --approved-by \"<Lead>\"` to commit selected tickets to Jira sprint backlog.")

        return self.format_output(summary, "Proposed Sprint Scope", findings_content)
