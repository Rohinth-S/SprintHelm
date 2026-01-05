"""
Unified Command-Line Interface (CLI) for CodinzHub Sprint Guardian.
Provides cross-platform execution for all 9 operational modes.
"""

import argparse
from pathlib import Path
import sys
from typing import Optional
from sprint_guardian.config import load_config
from sprint_guardian.governance import ApprovalGatekeeper, AuditLogger
from sprint_guardian.jira.mock_client import MockJiraClient
from sprint_guardian.jira.rest_client import RestJiraClient
from sprint_guardian.modes import MODE_REGISTRY


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sprint-guardian",
        description="CodinzHub Sprint Guardian - AI-Powered Agile Sprint Orchestrator",
    )
    parser.add_argument(
        "--mode",
        choices=list(MODE_REGISTRY.keys()),
        required=True,
        help="Operational mode to run.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Allow Jira mutations. Default is dry-run.",
    )
    parser.add_argument(
        "--approved-by",
        dest="approved_by",
        help="Authorized human signature for assignee changes.",
    )
    parser.add_argument(
        "--approval-note",
        dest="approval_note",
        help="Optional human approval rationale.",
    )
    parser.add_argument(
        "--board-id",
        dest="board_id",
        help="Jira board ID override.",
    )
    parser.add_argument(
        "--project-key",
        dest="project_key",
        help="Jira project key override.",
    )
    parser.add_argument(
        "--sprint-id",
        dest="sprint_id",
        help="Jira sprint ID override.",
    )
    parser.add_argument(
        "--sprint-name",
        dest="sprint_name",
        help="Sprint name for planning context.",
    )
    parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Sprint start date in ISO format.",
    )
    parser.add_argument(
        "--end-date",
        dest="end_date",
        help="Sprint end date in ISO format.",
    )
    parser.add_argument(
        "--issue-keys",
        dest="issue_keys",
        help="Comma-separated Jira issue keys.",
    )
    parser.add_argument(
        "--jql",
        dest="jql",
        help="Custom JQL query override.",
    )
    parser.add_argument(
        "--output-file",
        dest="output_file",
        help="Save generated markdown report to file.",
    )
    parser.add_argument(
        "--team-map",
        dest="team_map",
        help="Path to team-map.local.yaml override.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use in-memory mock Jira environment (default: True).",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.team_map)
    gatekeeper = ApprovalGatekeeper(config)
    audit_logger = AuditLogger()

    # Validation check for apply and approval
    mode_cls = MODE_REGISTRY.get(args.mode)
    if not mode_cls:
        sys.stderr.write(f"Error: Unknown mode '{args.mode}'\n")
        return 1

    report_only_modes = {"inspect-sprint", "surface-risk", "progress-pulse", "standup-brief", "retro-notes"}
    if args.apply and args.mode in report_only_modes:
        sys.stderr.write(f"Error: Mode '{args.mode}' is report-only and does not support --apply.\n")
        return 1

    jira_client = MockJiraClient() if args.mock else RestJiraClient()

    executor = mode_cls(
        config=config,
        jira_client=jira_client,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=args.apply,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
    )

    output = executor.execute(
        board_id=args.board_id,
        sprint_id=args.sprint_id,
        sprint_name=args.sprint_name,
        start_date=args.start_date,
        end_date=args.end_date,
        issue_keys=args.issue_keys,
        jql=args.jql,
    )

    if args.output_file:
        out_p = Path(args.output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(output, encoding="utf-8")
        print(f"Report saved to {out_p}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
