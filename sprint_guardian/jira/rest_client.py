"""
Direct Atlassian Jira Cloud/Server REST API client adapter.
"""

import base64
import json
import os
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.error
from sprint_guardian.jira.client import JiraClient
from sprint_guardian.models import JiraIssue, Sprint


class RestJiraClient(JiraClient):
    """
    Connects directly to Jira REST API v3 / Agile v1.0.
    Reads credentials from JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("JIRA_URL", "")).rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL", "")
        self.token = api_token or os.getenv("JIRA_API_TOKEN", "")

    def _get_headers(self) -> Dict[str, str]:
        auth_str = f"{self.email}:{self.token}"
        encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        return {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CodinzHub-Sprint-Guardian/1.0",
        }

    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{endpoint}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self._get_headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode("utf-8")
                return json.loads(content) if content else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"Jira API error {e.code}: {err_body}")

    def query_issues(self, jql: str) -> List[JiraIssue]:
        endpoint = f"/rest/api/3/search?jql={urllib.parse.quote(jql)}&maxResults=50"
        res = self._request("GET", endpoint)
        issues = []
        for raw in res.get("issues", []):
            f = raw.get("fields", {})
            issues.append(
                JiraIssue(
                    key=raw.get("key", ""),
                    summary=f.get("summary", ""),
                    status=(f.get("status") or {}).get("name", "To Do"),
                    status_category=((f.get("status") or {}).get("statusCategory") or {}).get("name", "To Do"),
                    priority=(f.get("priority") or {}).get("name", "Medium"),
                    assignee=((f.get("assignee") or {}).get("emailAddress") or (f.get("assignee") or {}).get("displayName")),
                    components=[c.get("name", "") for c in f.get("components", [])],
                    labels=f.get("labels", []),
                    story_points=int(f.get("customfield_10016") or f.get("customfield_10026") or 0),
                    updated=f.get("updated", ""),
                    created=f.get("created", ""),
                    duedate=f.get("duedate"),
                    description=str(f.get("description") or ""),
                )
            )
        return issues

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        endpoint = f"/rest/api/3/issue/{issue_key}"
        try:
            raw = self._request("GET", endpoint)
            f = raw.get("fields", {})
            return JiraIssue(
                key=raw.get("key", issue_key),
                summary=f.get("summary", ""),
                status=(f.get("status") or {}).get("name", "To Do"),
                status_category=((f.get("status") or {}).get("statusCategory") or {}).get("name", "To Do"),
                priority=(f.get("priority") or {}).get("name", "Medium"),
                assignee=((f.get("assignee") or {}).get("emailAddress") or (f.get("assignee") or {}).get("displayName")),
                components=[c.get("name", "") for c in f.get("components", [])],
                labels=f.get("labels", []),
                story_points=int(f.get("customfield_10016") or 0),
                updated=f.get("updated", ""),
                created=f.get("created", ""),
                duedate=f.get("duedate"),
                description=str(f.get("description") or ""),
            )
        except Exception:
            return None

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        endpoint = f"/rest/api/3/issue/{issue_key}"
        self._request("PUT", endpoint, {"fields": fields})
        return True

    def assign_issue(self, issue_key: str, assignee_email_or_name: str) -> bool:
        endpoint = f"/rest/api/3/issue/{issue_key}/assignee"
        self._request("PUT", endpoint, {"accountId": assignee_email_or_name})
        return True

    def get_sprints(self, board_id: str) -> List[Sprint]:
        endpoint = f"/rest/agile/1.0/board/{board_id}/sprint"
        res = self._request("GET", endpoint)
        sprints = []
        for s in res.get("values", []):
            sprints.append(
                Sprint(
                    id=str(s.get("id")),
                    name=s.get("name", ""),
                    board_id=str(board_id),
                    state=s.get("state", "active"),
                    start_date=s.get("startDate", ""),
                    end_date=s.get("endDate", ""),
                    goal=s.get("goal", ""),
                )
            )
        return sprints

    def get_active_sprint(self, board_id: str) -> Optional[Sprint]:
        sprints = self.get_sprints(board_id)
        for s in sprints:
            if s.state.lower() == "active":
                return s
        return None
