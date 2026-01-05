"""
Strongly typed domain models for Jira entities, team mappings, scoring breakdowns,
and governance audit records.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Any


class OperationalMode(str, Enum):
    SHAPE_SPRINT = "shape-sprint"
    TRIAGE_QUEUE = "triage-queue"
    SUGGEST_OWNER = "suggest-owner"
    BALANCE_LOAD = "balance-load"
    INSPECT_SPRINT = "inspect-sprint"
    SURFACE_RISK = "surface-risk"
    PROGRESS_PULSE = "progress-pulse"
    STANDUP_BRIEF = "standup-brief"
    RETRO_NOTES = "retro-notes"


class StatusCategory(str, Enum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class ConfidenceTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TriageCategory(str, Enum):
    READY = "Ready"
    NEEDS_INFO = "Needs Info"
    BLOCKED = "Blocked"
    DUPLICATE = "Duplicate / Link Needed"
    OWNER_NEEDED = "Owner Needed"
    SPRINT_CANDIDATE = "Sprint Candidate"


@dataclass
class TeamMember:
    name: str
    jira_assignee: str
    team: str = "CodinzHub"
    skills: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    max_in_progress: int = 3
    sprint_capacity_points: int = 10
    backup_assignee: Optional[str] = None
    unavailable_dates: List[str] = field(default_factory=list)
    assignment_allowlist: bool = True

    def matches_skill(self, skill: str) -> bool:
        normalized = skill.lower().strip()
        return any(normalized == s.lower().strip() for s in self.skills)

    def matches_component(self, component: str) -> bool:
        normalized = component.lower().strip()
        return any(normalized == c.lower().strip() for c in self.components)

    def matches_label(self, label: str) -> bool:
        normalized = label.lower().strip()
        return any(normalized == l.lower().strip() for l in self.labels)


@dataclass
class JiraIssue:
    key: str
    summary: str
    status: str
    status_category: str = "To Do"
    priority: str = "Medium"
    assignee: Optional[str] = None
    components: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    story_points: int = 0
    updated: str = ""
    created: str = ""
    duedate: Optional[str] = None
    description: str = ""
    blocked_by: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    sprint_id: Optional[str] = None
    acceptance_criteria: Optional[str] = None

    @property
    def is_blocked(self) -> bool:
        return self.status.lower() in ("blocked", "on hold") or len(self.blocked_by) > 0

    @property
    def is_in_progress(self) -> bool:
        return self.status.lower() in ("in progress", "in review", "testing")

    @property
    def is_done(self) -> bool:
        return self.status.lower() in ("done", "closed", "resolved") or self.status_category.lower() == "done"


@dataclass
class Sprint:
    id: str
    name: str
    board_id: str
    state: str = "active"  # active, future, closed
    start_date: str = ""
    end_date: str = ""
    goal: str = ""


@dataclass
class OwnerScoreBreakdown:
    candidate_email: str
    candidate_name: str
    total_score: int
    confidence: ConfidenceTier
    positive_signals: List[str] = field(default_factory=list)
    negative_signals: List[str] = field(default_factory=list)
    is_wip_exceeded: bool = False
    is_capacity_exceeded: bool = False
    has_hard_blocker: bool = False


@dataclass
class ReadinessScoreBreakdown:
    issue_key: str
    total_score: int
    is_ready: bool
    positive_signals: List[str] = field(default_factory=list)
    negative_signals: List[str] = field(default_factory=list)


@dataclass
class ApprovalRecord:
    issue_key: str
    previous_owner: Optional[str]
    proposed_owner: str
    confidence: ConfidenceTier
    reason: str
    risk: str
    authority_needed: str
    status: str = "PENDING APPROVAL"  # PENDING APPROVAL or APPROVED
    approved_by: Optional[str] = None
    approval_note: Optional[str] = None
    applied: bool = False
    timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_tsv(self) -> str:
        fields = [
            self.timestamp_utc,
            f"status={'completed' if self.applied else 'started'}",
            f"approved_by={self.approved_by or 'none'}",
            f"issue_keys={self.issue_key}",
            f"note={self.approval_note or 'none'}",
            f"previous={self.previous_owner or 'unassigned'}",
            f"target={self.proposed_owner}",
        ]
        return "\t".join(fields)
