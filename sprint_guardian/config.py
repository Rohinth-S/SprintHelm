"""
Configuration manager: parses team-map YAML and environment variables,
validating assigning authorities and WIP thresholds.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import yaml
from sprint_guardian.models import TeamMember


class ConfigError(Exception):
    """Raised when configuration validation fails."""
    pass


class TeamMapConfig:
    def __init__(self, raw_data: Dict[str, Any]):
        self.raw = raw_data
        self.board_id = str((raw_data.get("board") or {}).get("id", "1234"))
        self.project_keys: List[str] = (raw_data.get("board") or {}).get("project_keys", ["CodinzHub"])

        defaults = raw_data.get("defaults") or {}
        self.dry_run: bool = defaults.get("dry_run", True)
        self.stale_after_days: int = defaults.get("stale_after_days", 3)
        self.standup_lookback_days: int = defaults.get("standup_lookback_days", 1)
        self.blocked_statuses: List[str] = defaults.get("blocked_statuses", ["Blocked", "On Hold"])
        self.active_statuses: List[str] = defaults.get("active_statuses", ["In Progress", "In Review", "Testing"])
        self.done_statuses: List[str] = defaults.get("done_statuses", ["Done", "Closed", "Resolved"])
        self.backlog_jql: str = defaults.get("backlog_jql", "")
        self.active_sprint_jql: str = defaults.get("active_sprint_jql", "")

        approval = raw_data.get("approval") or {}
        self.assignee_change_requires_approval: bool = approval.get("assignee_change_requires_approval", True)
        self.allow_apply_without_approval: bool = approval.get("allow_apply_without_approval", False)
        self.audit_log_path: str = approval.get("audit_log", "automation/output/approvals.log")

        self.authorities: List[Dict[str, Any]] = approval.get("assigning_authorities") or []
        self._authorized_identities: Set[str] = set()
        for auth in self.authorities:
            if isinstance(auth, dict):
                for k in ("name", "jira_assignee"):
                    val = auth.get(k)
                    if isinstance(val, str) and val.strip():
                        self._authorized_identities.add(val.strip().lower())

        self.team_members: Dict[str, TeamMember] = {}
        for item in raw_data.get("team") or []:
            if isinstance(item, dict):
                member = TeamMember(
                    name=item.get("name", "Unknown"),
                    jira_assignee=item.get("jira_assignee", ""),
                    team=item.get("team", "CodinzHub"),
                    skills=item.get("skills", []),
                    components=item.get("components", []),
                    labels=item.get("labels", []),
                    max_in_progress=item.get("max_in_progress", 3),
                    sprint_capacity_points=item.get("sprint_capacity_points", 10),
                    backup_assignee=item.get("backup_assignee"),
                    unavailable_dates=item.get("unavailable_dates", []),
                    assignment_allowlist=item.get("assignment_allowlist", True),
                )
                self.team_members[member.jira_assignee.lower()] = member

        rules = raw_data.get("rules") or {}
        self.never_auto_assign_labels: Set[str] = set(rules.get("never_auto_assign_labels", []))
        self.cross_team_approval: bool = rules.get("cross_team_assignment_requires_approval", True)

    def is_authorized(self, approver: Optional[str]) -> bool:
        if not approver:
            return False
        return approver.strip().lower() in self._authorized_identities

    def get_member(self, email_or_name: str) -> Optional[TeamMember]:
        query = email_or_name.strip().lower()
        if query in self.team_members:
            return self.team_members[query]
        for m in self.team_members.values():
            if m.name.lower() == query:
                return m
        return None

    def get_all_members(self) -> List[TeamMember]:
        return list(self.team_members.values())


def load_config(custom_path: Optional[str] = None) -> TeamMapConfig:
    """Load and validate the team-map configuration."""
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path))
    candidates.extend([
        Path("references/team-map.local.yaml"),
        Path("references/team-map.example.yaml"),
        Path(__file__).parent.parent / "references/team-map.local.yaml",
        Path(__file__).parent.parent / "references/team-map.example.yaml",
    ])

    for p in candidates:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return TeamMapConfig(data)

    # Return default fallback
    return TeamMapConfig({
        "board": {"id": "1234", "project_keys": ["CodinzHub"]},
        "defaults": {"dry_run": True, "stale_after_days": 3},
        "approval": {
            "assignee_change_requires_approval": True,
            "assigning_authorities": [{"name": "Coder Coder", "jira_assignee": "coder.coder@codinzhub.com"}]
        },
        "team": [
            {
                "name": "Coder Coder",
                "jira_assignee": "coder.coder@codinzhub.com",
                "skills": ["codinzhub", "lead", "automation"],
                "components": ["CodinzHub"],
                "max_in_progress": 3,
                "sprint_capacity_points": 15,
                "assignment_allowlist": True
            }
        ]
    })
