"""
Unit tests for MockJiraClient and JQL query evaluator.
"""


def test_mock_jira_loads_sprints_and_issues(mock_jira):
    sprints = mock_jira.get_sprints("1234")
    assert len(sprints) >= 1
    active = mock_jira.get_active_sprint("1234")
    assert active is not None
    assert active.state == "active"


def test_mock_jira_jql_queries(mock_jira):
    # Active sprint issues
    open_sprint_issues = mock_jira.query_issues("sprint in openSprints()")
    assert len(open_sprint_issues) >= 1

    # Backlog unassigned
    unassigned = mock_jira.query_issues("assignee is EMPTY")
    assert len(unassigned) >= 1
    for u in unassigned:
        assert u.assignee is None


def test_mock_jira_mutations(mock_jira):
    target = "CodinzHub-108"
    assert mock_jira.get_issue(target) is not None
    res = mock_jira.assign_issue(target, "engineer.one@example.com")
    assert res is True
    updated = mock_jira.get_issue(target)
    assert updated.assignee == "engineer.one@example.com"
