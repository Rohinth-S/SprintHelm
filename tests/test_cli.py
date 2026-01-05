"""
Unit tests for CLI interface and MCP server.
"""

from sprint_guardian.cli import main
from sprint_guardian.mcp_server import SprintGuardianMCPServer


def test_cli_execution_standup(capsys):
    ret = main(["--mode", "standup-brief", "--mock"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Daily Agile Standup Brief" in captured.out


def test_cli_report_only_mode_rejects_apply(capsys):
    ret = main(["--mode", "inspect-sprint", "--apply", "--mock"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "report-only and does not support --apply" in captured.err


def test_mcp_server_tool_definitions():
    server = SprintGuardianMCPServer()
    tools = server.get_tool_definitions()
    tool_names = [t["name"] for t in tools]
    assert "sprint_guardian_run_mode" in tool_names
    assert "sprint_guardian_standup_brief" in tool_names
    assert "sprint_guardian_balance_load" in tool_names


def test_mcp_server_handle_call_tool():
    server = SprintGuardianMCPServer()
    res = server.handle_call_tool("sprint_guardian_standup_brief", {})
    assert "Daily Agile Standup Brief" in res
