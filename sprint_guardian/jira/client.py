"""
Abstract base class defining the Jira Client interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from sprint_guardian.models import JiraIssue, Sprint


class JiraClient(ABC):
    """Abstract interface for all Jira data access and mutation adapters."""

    @abstractmethod
    def query_issues(self, jql: str) -> List[JiraIssue]:
        """Execute a JQL query and return matching Jira issues."""
        pass

    @abstractmethod
    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Fetch a specific Jira issue by key."""
        pass

    @abstractmethod
    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """Update fields on a Jira issue."""
        pass

    @abstractmethod
    def assign_issue(self, issue_key: str, assignee_email_or_name: str) -> bool:
        """Update assignee on a Jira issue."""
        pass

    @abstractmethod
    def get_sprints(self, board_id: str) -> List[Sprint]:
        """Fetch all sprints for a board."""
        pass

    @abstractmethod
    def get_active_sprint(self, board_id: str) -> Optional[Sprint]:
        """Fetch the current open/active sprint for a board."""
        pass
