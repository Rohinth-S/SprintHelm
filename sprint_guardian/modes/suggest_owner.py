"""
Mode: codinzhub-suggest-owner
Recommends optimal assignee with score breakdown, alternative candidates,
and human-in-the-loop approval gate.
"""

from typing import List, Optional
from sprint_guardian.models import OperationalMode, JiraIssue, ConfidenceTier
from sprint_guardian.modes.base import BaseMode
from sprint_guardian.scoring import OwnershipScorer


class SuggestOwnerMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.SUGGEST_OWNER, **kwargs)

    def execute(self, issue_keys: Optional[str] = None, **kwargs) -> str:
        keys = [k.strip() for k in (issue_keys or "").split(",") if k.strip()]
        if not keys:
            # Look for unassigned issues in active sprint or backlog
            query = f"project in ({','.join(self.config.project_keys)}) AND assignee is EMPTY AND statusCategory != Done ORDER BY priority DESC"
            issues = self.jira.query_issues(query)
        else:
            issues = [self.jira.get_issue(k) for k in keys if self.jira.get_issue(k)]

        if not issues:
            return self.format_output(
                "No unassigned or requested issues found to evaluate for ownership.",
                "Ownership Evaluation",
                "No target issues identified. Please pass `--issue-keys <KEY>` or ensure unassigned backlog issues exist.",
            )

        team = self.config.get_all_members()
        active_sprint_issues = self.jira.query_issues("sprint in openSprints() AND statusCategory != Done")

        findings_lines = [
            "### Assignee Recommendation Matrix",
            "",
            "| Issue Key | Current Owner | Recommended Owner | Score | Confidence | Primary Rationale | Alternative |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        evaluated_count = 0

        for issue in issues:
            evaluated_count += 1
            scores = []
            for candidate in team:
                active_for_cand = [i for i in active_sprint_issues if i.assignee == candidate.jira_assignee and i.is_in_progress]
                score_breakdown = OwnershipScorer.score_candidate(issue, candidate, active_for_cand)
                scores.append((candidate, score_breakdown))

            # Sort descending by score
            scores.sort(key=lambda x: x[1].total_score, reverse=True)
            top_cand, top_sb = scores[0]
            runner_up = scores[1] if len(scores) > 1 else None

            alt_str = f"{runner_up[0].name} ({runner_up[1].total_score})" if runner_up else "None"
            reason_str = ", ".join(top_sb.positive_signals) or "General team capacity"
            findings_lines.append(
                f"| `{issue.key}` | `{issue.assignee or 'Unassigned'}` | **{top_cand.name}** (`{top_cand.jira_assignee}`) | "
                f"+{top_sb.total_score} | `{top_sb.confidence.value.upper()}` | {reason_str} | {alt_str} |"
            )

            # Check approval gate
            can_mutate = self.gatekeeper.verify_assignee_change(
                self.mode, self.apply, self.approved_by, top_sb.confidence, top_sb.has_hard_blocker
            )

            if can_mutate:
                self.jira.assign_issue(issue.key, top_cand.jira_assignee)
                rec = self.gatekeeper.create_approved_item(
                    issue_key=issue.key,
                    current_owner=issue.assignee,
                    proposed_owner=top_cand.jira_assignee,
                    confidence=top_sb.confidence,
                    reason=f"Top candidate score +{top_sb.total_score}: {reason_str}",
                    approved_by=self.approved_by,
                    approval_note=self.approval_note,
                )
                self.approval_records.append(rec)
                self.audit_logger.log_approval(rec)
            else:
                risk_note = "Awaiting formal assigning authority sign-off"
                if top_sb.has_hard_blocker:
                    risk_note = f"Hard blocker: {', '.join(top_sb.negative_signals)}"
                    self.risks.append(f"{issue.key} -> {top_cand.name}: {risk_note}")

                rec = self.gatekeeper.create_pending_approval_item(
                    issue_key=issue.key,
                    current_owner=issue.assignee,
                    proposed_owner=top_cand.jira_assignee,
                    confidence=top_sb.confidence,
                    reason=f"Affinity score +{top_sb.total_score} ({reason_str})",
                    risk=risk_note,
                )
                self.approval_records.append(rec)

        summary = (
            f"Evaluated ownership affinity across **{evaluated_count} issue(s)** for team of {len(team)} engineers. "
            f"Generated {len(self.approval_records)} candidate assignments "
            f"({sum(1 for r in self.approval_records if r.applied)} applied, "
            f"{sum(1 for r in self.approval_records if not r.applied)} pending approval)."
        )

        if not self.apply:
            self.recommended_actions.append(
                f"Review pending ownership recommendations above and re-run with `--apply --approved-by \"<Assigning Authority>\"` to commit changes to Jira."
            )
        else:
            self.recommended_actions.append("All approved assignee mutations have been written to Jira and logged in audit trail.")

        return self.format_output(summary, "Owner Suggestions", "\n".join(findings_lines))
