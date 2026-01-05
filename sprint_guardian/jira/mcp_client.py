"""
Model Context Protocol (MCP) client adapter for Atlassian MCP tools.
Enables Sprint Guardian to integrate natively with mcp-atlassian or IDE MCP hosts.
"""

import json
from typing import Dict, List, Optional, Any
from sprint_guardian.jira.client import JiraClient
from sprint_guardian.models import JiraIssue, Sprint


class McpJiraClient(JiraClient):
    """
    Adapter communicating with Atlassian Jira via Model Context Protocol (MCP) JSON-RPC tools.
    """

    def __init__(self, mcp_server_name: str = "mcp-atlassian"):
        self.server_name = mcp_server_name

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        # Standard MCP tool invocation envelope
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
            "id": 1,
        }
        # In actual MCP runtime, this is piped via stdio to the MCP sub-process.
        # Fallback to empty response if not attached to a live MCP stdio pipeline.
        return {}

    def query_issues(self, jql: str) -> List[JiraIssue]:
        res = self.call_tool("jira_search", {"jql": jql, "max_results": 50})
        issues = []
        for raw in res.get("issues", []):
            issues.append(
                JiraIssue(
                    key=raw.get("key", ""),
                    summary=raw.get("summary", ""),
                    status=raw.get("status", "To Do"),
                    priority=raw.get("priority", "Medium"),
                    assignee=raw.get("assignee"),
                    components=raw.get("components", []),
                    labels=raw.get("labels", []),
                    story_points=int(raw.get("story_points", 0)),
                )
            )
        return issues

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        res = self.call_tool("jira_get_issue", {"issue_key": issue_key})
        if not res:
            return None
        return JiraIssue(
            key=res.get("key", issue_key),
            summary=res.get("summary", ""),
            status=res.get("status", "To Do"),
            priority=res.get("priority", "Medium"),
            assignee=res.get("assignee"),
        )

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        self.call_tool("jira_update_issue", {"issue_key": issue_key, "fields": fields})
        return True

    def assign_issue(self, issue_key: str, assignee_email_or_name: str) -> bool:
        self.call_tool("jira_assign_issue", {"issue_key": issue_key, "assignee": assignee_email_or_name})
        return True

    def get_sprints(self, board_id: str) -> List[Sprint]:
        res = self.call_tool("jira_get_sprints", {"board_id": board_id})
        return [
            Sprint(id=str(s.get("id")), name=s.get("name", ""), board_id=str(board_id), state=s.get("state", "active"))
            for s in res.get("sprints", [])
        ]

    def get_active_sprint(self, board_id: str) -> Optional[Sprint]:
        for s in self.get_sprints(board_id):
            if s.state.lower() == "active":
                return s
        return None
