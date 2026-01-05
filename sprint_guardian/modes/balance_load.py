"""
Mode: codinzhub-balance-load
Analyzes active sprint work distribution, flags overloaded engineers,
and recommends safe reassignment balancing WIP limits and story points.
"""

from typing import Dict, List, Optional, Tuple
from sprint_guardian.models import OperationalMode, JiraIssue, TeamMember, ConfidenceTier
from sprint_guardian.modes.base import BaseMode
from sprint_guardian.scoring import OwnershipScorer


class BalanceLoadMode(BaseMode):
    def __init__(self, **kwargs):
        super().__init__(mode=OperationalMode.BALANCE_LOAD, **kwargs)

    def execute(self, board_id: Optional[str] = None, sprint_id: Optional[str] = None, **kwargs) -> str:
        bid = board_id or self.config.board_id
        active_sprint = self.jira.get_active_sprint(bid)
        query = f"project in ({','.join(self.config.project_keys)}) AND sprint in openSprints() AND statusCategory != Done ORDER BY assignee ASC, priority DESC"
        sprint_issues = self.jira.query_issues(query)
        team = self.config.get_all_members()

        # Group issues by assignee
        workload: Dict[str, List[JiraIssue]] = {m.jira_assignee.lower(): [] for m in team}
        unassigned: List[JiraIssue] = []

        for issue in sprint_issues:
            if issue.assignee and issue.assignee.lower() in workload:
                workload[issue.assignee.lower()].append(issue)
            else:
                unassigned.append(issue)

        # Capacity and WIP analysis
        overloaded: List[Tuple[TeamMember, List[JiraIssue], int, int]] = []
        underutilized: List[Tuple[TeamMember, List[JiraIssue], int, int]] = []

        for member in team:
            member_issues = workload.get(member.jira_assignee.lower(), [])
            in_prog_count = len([i for i in member_issues if i.is_in_progress])
            total_pts = sum(i.story_points for i in member_issues)

            if in_prog_count > member.max_in_progress or total_pts > member.sprint_capacity_points:
                overloaded.append((member, member_issues, in_prog_count, total_pts))
            elif in_prog_count < member.max_in_progress and total_pts < member.sprint_capacity_points:
                underutilized.append((member, member_issues, in_prog_count, total_pts))

        findings_lines = [
            "### Current Team Workload & WIP Distribution",
            "",
            "| Engineer | Active WIP | Max WIP Limit | Sprint Points | Capacity Limit | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]

        for member in team:
            issues = workload.get(member.jira_assignee.lower(), [])
            wip = len([i for i in issues if i.is_in_progress])
            pts = sum(i.story_points for i in issues)
            is_over = wip > member.max_in_progress or pts > member.sprint_capacity_points
            status_badge = "🔴 **OVERLOADED**" if is_over else "🟢 Optimal"
            findings_lines.append(
                f"| **{member.name}** (`{member.jira_assignee}`) | {wip} tickets | {member.max_in_progress} | {pts} pts | {member.sprint_capacity_points} pts | {status_badge} |"
            )

        # Generate rebalancing proposals
        moves_proposed = 0
        if overloaded and underutilized:
            findings_lines.extend([
                "",
                "### Proposed Workload Reassignment Plan",
                "",
                "| Issue Key | Summary | Current Overloaded Owner | Target Available Owner | Affinity Reason |",
                "| :--- | :--- | :--- | :--- | :--- |",
            ])

            for over_member, over_issues, _, _ in overloaded:
                # Find moveable tickets (not blocked, in progress)
                candidates_to_move = [i for i in over_issues if not i.is_blocked]
                for ticket in candidates_to_move:
                    # Find best recipient among underutilized
                    best_target = None
                    best_score = -10
                    for under_member, under_issues, uwip, upts in underutilized:
                        if uwip >= under_member.max_in_progress:
                            continue
                        sb = OwnershipScorer.score_candidate(ticket, under_member, under_issues)
                        if sb.total_score > best_score and not sb.has_hard_blocker:
                            best_score = sb.total_score
                            best_target = (under_member, sb)

                    if best_target:
                        target_member, sb = best_target
                        moves_proposed += 1
                        reason_desc = f"+{sb.total_score} pts: {', '.join(sb.positive_signals)}"
                        findings_lines.append(
                            f"| `{ticket.key}` | {ticket.summary} | `{over_member.name}` | `{target_member.name}` | {reason_desc} |"
                        )

                        # Check approval gate
                        can_mutate = self.gatekeeper.verify_assignee_change(
                            self.mode, self.apply, self.approved_by, sb.confidence, sb.has_hard_blocker
                        )

                        if can_mutate:
                            self.jira.assign_issue(ticket.key, target_member.jira_assignee)
                            rec = self.gatekeeper.create_approved_item(
                                issue_key=ticket.key,
                                current_owner=over_member.jira_assignee,
                                proposed_owner=target_member.jira_assignee,
                                confidence=sb.confidence,
                                reason=f"Workload rebalance: {reason_desc}",
                                approved_by=self.approved_by,
                                approval_note=self.approval_note,
                            )
                            self.approval_records.append(rec)
                            self.audit_logger.log_approval(rec)
                        else:
                            rec = self.gatekeeper.create_pending_approval_item(
                                issue_key=ticket.key,
                                current_owner=over_member.jira_assignee,
                                proposed_owner=target_member.jira_assignee,
                                confidence=sb.confidence,
                                reason=f"Workload rebalancing recommendation ({reason_desc})",
                                risk="Pending human lead sign-off before mutating active sprint assignment",
                            )
                            self.approval_records.append(rec)

                        # Only move 1-2 tickets per overloaded engineer to prevent churn
                        break

        summary = (
            f"Analyzed active sprint workload across {len(team)} team members ({len(sprint_issues)} active issues). "
            f"Identified **{len(overloaded)} overloaded engineer(s)** and **{len(underutilized)} team member(s) with available capacity**. "
            f"Generated **{moves_proposed} workload rebalancing proposal(s)**."
        )

        if overloaded:
            for m, _, wip, pts in overloaded:
                self.risks.append(f"{m.name} is overloaded (WIP: {wip}/{m.max_in_progress}, Points: {pts}/{m.sprint_capacity_points}).")

        if moves_proposed > 0 and not self.apply:
            self.recommended_actions.append(
                f"Execute with `--apply --approved-by \"<Assigning Authority>\"` to apply the {moves_proposed} workload rebalancing moves in Jira."
            )

        return self.format_output(summary, "Workload Load Balance Analysis", "\n".join(findings_lines))
