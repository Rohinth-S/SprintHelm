"""
Model Context Protocol (MCP) Server for CodinzHub Sprint Guardian.
Exposes sprint coordination and governance tools to AI assistants (Claude, Codex, Cursor, Antigravity).
"""

import json
import sys
from typing import Any, Dict, List
from sprint_guardian.config import load_config
from sprint_guardian.governance import ApprovalGatekeeper, AuditLogger
from sprint_guardian.jira.mock_client import MockJiraClient
from sprint_guardian.modes import MODE_REGISTRY


class SprintGuardianMCPServer:
    """Standard Model Context Protocol Server (stdio JSON-RPC transport)."""

    def __init__(self):
        self.config = load_config()
        self.jira = MockJiraClient()
        self.gatekeeper = ApprovalGatekeeper(self.config)
        self.audit_logger = AuditLogger()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "sprint_guardian_run_mode",
                "description": "Execute any of the 9 CodinzHub Sprint Guardian operational modes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": list(MODE_REGISTRY.keys()),
                            "description": "The operational mode to execute.",
                        },
                        "apply": {
                            "type": "boolean",
                            "description": "Whether to apply Jira mutations (requires approval for assignee changes).",
                            "default": False,
                        },
                        "approved_by": {
                            "type": "string",
                            "description": "Authorized assigning authority signature.",
                        },
                        "issue_keys": {
                            "type": "string",
                            "description": "Comma-separated issue keys (e.g. CodinzHub-101).",
                        },
                        "board_id": {
                            "type": "string",
                            "description": "Jira board ID override.",
                        },
                    },
                    "required": ["mode"],
                },
            },
            {
                "name": "sprint_guardian_standup_brief",
                "description": "Compile daily sprint status summary for the engineering team.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "board_id": {"type": "string", "description": "Optional board ID."},
                    },
                },
            },
            {
                "name": "sprint_guardian_balance_load",
                "description": "Audit team WIP distribution and generate load balancing recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "apply": {"type": "boolean", "default": False},
                        "approved_by": {"type": "string"},
                    },
                },
            },
        ]

    def handle_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        mode_str = "standup-brief"
        if tool_name == "sprint_guardian_run_mode":
            mode_str = arguments.get("mode", "standup-brief")
        elif tool_name == "sprint_guardian_balance_load":
            mode_str = "balance-load"
        elif tool_name == "sprint_guardian_standup_brief":
            mode_str = "standup-brief"

        mode_cls = MODE_REGISTRY.get(mode_str)
        if not mode_cls:
            raise ValueError(f"Unknown operational mode: {mode_str}")

        executor = mode_cls(
            config=self.config,
            jira_client=self.jira,
            gatekeeper=self.gatekeeper,
            audit_logger=self.audit_logger,
            apply=arguments.get("apply", False),
            approved_by=arguments.get("approved_by"),
        )
        return executor.execute(**arguments)

    def run_stdio(self) -> None:
        """Run standard stdio line-oriented JSON-RPC loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                method = request.get("method")
                req_id = request.get("id")

                if method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"tools": self.get_tool_definitions()},
                    }
                elif method == "tools/call":
                    params = request.get("params", {})
                    name = params.get("name")
                    args = params.get("arguments", {})
                    output = self.handle_call_tool(name, args)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {"content": [{"type": "text", "text": output}]},
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {},
                    }
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


def main():
    server = SprintGuardianMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
