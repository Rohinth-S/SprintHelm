"""
In-memory Mock Jira Client loaded with realistic test data.
Supports offline testing, automated unit tests, and CI/CD pipelines without live Jira tokens.
"""

from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Any
from sprint_guardian.jira.client import JiraClient
from sprint_guardian.models import JiraIssue, Sprint


class MockJiraClient(JiraClient):
    def __init__(self, dataset_path: Optional[str] = None):
        self.issues: Dict[str, JiraIssue] = {}
        self.sprints: Dict[str, Sprint] = {}
        self.board_info: Dict[str, Any] = {}
        self._load_dataset(dataset_path)

    def _load_dataset(self, dataset_path: Optional[str]) -> None:
        candidates = []
        if dataset_path:
            candidates.append(Path(dataset_path))
        candidates.extend([
            Path("samples/mock_sprint_dataset.json"),
            Path(__file__).parent.parent.parent / "samples/mock_sprint_dataset.json",
        ])

        data = None
        for p in candidates:
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    break

        if not data:
            # Fallback basic dataset
            data = {
                "board": {"id": "1234", "name": "CodinzHub Board"},
                "sprints": [{"id": "4567", "name": "Sprint 24 - Core Pipeline", "board_id": "1234", "state": "active"}],
                "issues": [
                    {
                        "key": "CodinzHub-101",
                        "summary": "Core Sprint Guardian Engine",
                        "status": "In Progress",
                        "status_category": "In Progress",
                        "priority": "Highest",
                        "assignee": "coder.coder@codinzhub.com",
                        "components": ["CodinzHub"],
                        "labels": ["codinzhub", "lead"],
                        "story_points": 5,
                        "updated": "2026-05-26T14:00:00Z",
                        "created": "2026-05-20T10:00:00Z",
                        "description": "Core orchestration engine.",
                        "acceptance_criteria": "Passes all tests.",
                        "sprint_id": "4567",
                    }
                ]
            }

        self.board_info = data.get("board", {})
        for s in data.get("sprints", []):
            sprint_obj = Sprint(
                id=str(s["id"]),
                name=s["name"],
                board_id=str(s.get("board_id", self.board_info.get("id", "1234"))),
                state=s.get("state", "active"),
                start_date=s.get("start_date", ""),
                end_date=s.get("end_date", ""),
                goal=s.get("goal", ""),
            )
            self.sprints[sprint_obj.id] = sprint_obj

        for i in data.get("issues", []):
            issue_obj = JiraIssue(
                key=i["key"],
                summary=i["summary"],
                status=i["status"],
                status_category=i.get("status_category", "To Do"),
                priority=i.get("priority", "Medium"),
                assignee=i.get("assignee"),
                components=i.get("components", []),
                labels=i.get("labels", []),
                story_points=i.get("story_points", 0),
                updated=i.get("updated", "2026-05-26T12:00:00Z"),
                created=i.get("created", "2026-05-20T10:00:00Z"),
                duedate=i.get("duedate"),
                description=i.get("description", ""),
                blocked_by=i.get("blocked_by", []),
                blocks=i.get("blocks", []),
                sprint_id=str(i["sprint_id"]) if i.get("sprint_id") else None,
                acceptance_criteria=i.get("acceptance_criteria"),
            )
            self.issues[issue_obj.key] = issue_obj

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        return self.issues.get(issue_key.strip())

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        issue = self.get_issue(issue_key)
        if not issue:
            return False
        for k, v in fields.items():
            if hasattr(issue, k):
                setattr(issue, k, v)
        issue.updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return True

    def assign_issue(self, issue_key: str, assignee_email_or_name: str) -> bool:
        return self.update_issue(issue_key, {"assignee": assignee_email_or_name.strip()})

    def get_sprints(self, board_id: str) -> List[Sprint]:
        return [s for s in self.sprints.values() if s.board_id == str(board_id)]

    def get_active_sprint(self, board_id: str) -> Optional[Sprint]:
        for s in self.sprints.values():
            if s.board_id == str(board_id) and s.state.lower() == "active":
                return s
        return None

    def query_issues(self, jql: str) -> List[JiraIssue]:
        """Simple evaluator for common CodinzHub JQL expressions."""
        results = list(self.issues.values())
        query = jql.lower()

        # Sprint filtering
        if "sprint in opensprints()" in query:
            active_sprint = next((s for s in self.sprints.values() if s.state == "active"), None)
            if active_sprint:
                results = [i for i in results if i.sprint_id == active_sprint.id]
            else:
                results = [i for i in results if i.sprint_id is not None]
        elif "sprint is empty" in query:
            results = [i for i in results if not i.sprint_id]
        elif "sprint in closedsprints()" in query:
            closed_sprints = {s.id for s in self.sprints.values() if s.state == "closed"}
            results = [i for i in results if i.sprint_id in closed_sprints]
        elif "sprint =" in query:
            match = re.search(r"sprint\s*=\s*(\d+)", query)
            if match:
                sid = match.group(1)
                results = [i for i in results if i.sprint_id == sid]

        # Status category filtering
        if "statuscategory != done" in query:
            results = [i for i in results if not i.is_done]
        elif "statuscategory = done" in query:
            results = [i for i in results if i.is_done]

        # Assignee filtering
        if "assignee is empty" in query:
            results = [i for i in results if not i.assignee]
        elif "assignee is not empty" in query:
            results = [i for i in results if i.assignee]

        # Priority sorting
        priority_map = {"highest": 5, "high": 4, "medium": 3, "low": 2, "lowest": 1}
        if "order by priority desc" in query:
            results.sort(key=lambda x: priority_map.get(x.priority.lower(), 3), reverse=True)
        elif "order by rank asc" in query:
            results.sort(key=lambda x: x.key)
        elif "order by updated asc" in query:
            results.sort(key=lambda x: x.updated)
        elif "order by updated desc" in query:
            results.sort(key=lambda x: x.updated, reverse=True)

        return results
