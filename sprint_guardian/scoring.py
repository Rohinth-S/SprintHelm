"""
Mathematical scoring models for Jira Assignee Ownership and Sprint Readiness.
Adheres strictly to the weights defined in references/ownership-policy.md.
"""

from typing import List, Optional
from sprint_guardian.models import (
    JiraIssue,
    TeamMember,
    OwnerScoreBreakdown,
    ReadinessScoreBreakdown,
    ConfidenceTier,
)


class OwnershipScorer:
    """
    Computes candidate affinity score:
    Positive signals:
      +4 component ownership
      +3 label or feature-area ownership
      +3 skill match
      +2 recent similar work or git/PR activity
      +1 backup owner
    Negative signals:
      -5 not in assignment allowlist (hard blocker)
      -4 unavailable in sprint window (hard blocker)
      -4 at or above WIP limit (hard blocker)
      -3 above sprint capacity
      -3 move outside ownership map without routing rule
      -2 blocked issue where candidate cannot clear blocker
      -2 weak issue description or missing acceptance criteria
    """

    @staticmethod
    def score_candidate(
        issue: JiraIssue,
        candidate: TeamMember,
        active_issues_for_candidate: List[JiraIssue],
        sprint_window_dates: Optional[List[str]] = None,
        is_backup: bool = False,
        recent_activity: bool = False,
    ) -> OwnerScoreBreakdown:
        score = 0
        positives: List[str] = []
        negatives: List[str] = []
        hard_blocker = False

        # Positive evaluation
        comp_match = any(candidate.matches_component(c) for c in issue.components)
        if comp_match:
            score += 4
            positives.append("+4 component ownership")

        label_match = any(candidate.matches_label(l) for l in issue.labels)
        if label_match:
            score += 3
            positives.append("+3 label / feature area ownership")

        skill_match = any(candidate.matches_skill(s) for s in issue.labels + issue.components)
        if skill_match:
            score += 3
            positives.append("+3 skill match")

        if recent_activity:
            score += 2
            positives.append("+2 recent commit/PR activity")

        if is_backup:
            score += 1
            positives.append("+1 backup owner designation")

        # Negative evaluation
        if not candidate.assignment_allowlist:
            score -= 5
            negatives.append("-5 candidate not on assignment allowlist")
            hard_blocker = True

        if sprint_window_dates:
            unavailable_overlap = any(d in candidate.unavailable_dates for d in sprint_window_dates)
            if unavailable_overlap:
                score -= 4
                negatives.append("-4 candidate unavailable in sprint window")
                hard_blocker = True

        wip_count = len(active_issues_for_candidate)
        wip_exceeded = wip_count >= candidate.max_in_progress
        if wip_exceeded:
            score -= 4
            negatives.append(f"-4 candidate at/above WIP limit ({wip_count}/{candidate.max_in_progress})")
            hard_blocker = True

        current_points = sum(i.story_points for i in active_issues_for_candidate)
        capacity_exceeded = (current_points + issue.story_points) > candidate.sprint_capacity_points
        if capacity_exceeded:
            score -= 3
            negatives.append(f"-3 exceeds sprint capacity ({current_points + issue.story_points}/{candidate.sprint_capacity_points} pts)")

        if not comp_match and not label_match and not skill_match:
            score -= 3
            negatives.append("-3 move outside team ownership map")

        if issue.is_blocked:
            score -= 2
            negatives.append("-2 issue is blocked")

        if not issue.description or len(issue.description.strip()) < 20 or not issue.acceptance_criteria:
            score -= 2
            negatives.append("-2 weak description or missing acceptance criteria")

        # Determine confidence tier
        if hard_blocker or score < 3:
            confidence = ConfidenceTier.LOW
        elif score >= 6 and not hard_blocker and not capacity_exceeded:
            confidence = ConfidenceTier.HIGH
        else:
            confidence = ConfidenceTier.MEDIUM

        return OwnerScoreBreakdown(
            candidate_email=candidate.jira_assignee,
            candidate_name=candidate.name,
            total_score=score,
            confidence=confidence,
            positive_signals=positives,
            negative_signals=negatives,
            is_wip_exceeded=wip_exceeded,
            is_capacity_exceeded=capacity_exceeded,
            has_hard_blocker=hard_blocker,
        )


class ReadinessScorer:
    """
    Computes Sprint Readiness Score:
    Positive signals:
      +4 high priority or release-critical
      +3 clear owner with med/high confidence
      +2 defined acceptance criteria
      +2 dependencies are clear or unblocked
      +1 stale but still relevant need
    Negative signals:
      -5 blocked
      -4 no safe owner
      -3 missing description or acceptance criteria
      -3 unclear dependency
      -2 too large for remaining capacity
    """

    @staticmethod
    def score_readiness(
        issue: JiraIssue,
        has_safe_owner: bool = True,
        dependencies_unblocked: bool = True,
        is_oversized: bool = False,
    ) -> ReadinessScoreBreakdown:
        score = 0
        positives: List[str] = []
        negatives: List[str] = []

        if issue.priority.lower() in ("highest", "high"):
            score += 4
            positives.append("+4 high priority / release-critical")

        if has_safe_owner:
            score += 3
            positives.append("+3 clear owner with medium/high confidence")
        else:
            score -= 4
            negatives.append("-4 no safe owner identified")

        if issue.acceptance_criteria and len(issue.acceptance_criteria.strip()) > 10:
            score += 2
            positives.append("+2 defined acceptance criteria")
        else:
            score -= 3
            negatives.append("-3 missing acceptance criteria")

        if dependencies_unblocked and not issue.is_blocked:
            score += 2
            positives.append("+2 dependencies clear / unblocked")
        else:
            score -= 5
            negatives.append("-5 issue or dependency is blocked")

        if is_oversized:
            score -= 2
            negatives.append("-2 too large for sprint capacity (>8 pts)")

        is_ready = score >= 5 and not issue.is_blocked and has_safe_owner

        return ReadinessScoreBreakdown(
            issue_key=issue.key,
            total_score=score,
            is_ready=is_ready,
            positive_signals=positives,
            negative_signals=negatives,
        )
