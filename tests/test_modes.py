"""
Comprehensive integration tests covering all 9 operational modes.
"""

from sprint_guardian.modes import MODE_REGISTRY


def test_all_nine_modes_registered():
    expected_modes = [
        "shape-sprint",
        "triage-queue",
        "suggest-owner",
        "balance-load",
        "inspect-sprint",
        "surface-risk",
        "progress-pulse",
        "standup-brief",
        "retro-notes",
    ]
    for mode in expected_modes:
        assert mode in MODE_REGISTRY


def test_standup_brief_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["standup-brief"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Daily Agile Standup Brief" in output
    assert "## 1. Summary" in output
    assert "## 2. Daily Standup Synthesis" in output
    assert "## 3. Assignment Approval Items" in output
    assert "## 4. Recommended Jira Actions" in output
    assert "## 5. Missing Inputs or Risks" in output


def test_triage_queue_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["triage-queue"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Backlog Queue Classification" in output
    assert "Sprint Candidates" in output
    assert "Needs Information" in output


def test_suggest_owner_dry_run_vs_apply(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["suggest-owner"]

    # Dry-run
    dry_exec = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    dry_out = dry_exec.execute(issue_keys="CodinzHub-108")
    assert "PENDING APPROVAL: CodinzHub-108" in dry_out

    # Apply with valid approval
    apply_exec = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=True,
        approved_by="Rohinth S",
    )
    apply_out = apply_exec.execute(issue_keys="CodinzHub-108")
    assert "APPROVED: CodinzHub-108" in apply_out


def test_balance_load_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["balance-load"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Workload Load Balance Analysis" in output
    assert "Current Team Workload & WIP Distribution" in output


def test_inspect_sprint_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["inspect-sprint"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Sprint Health Inspection Findings" in output
    assert "Velocity Progress" in output


def test_surface_risk_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["surface-risk"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Delivery Risk Radar" in output


def test_progress_pulse_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["progress-pulse"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Sprint Pulse Snapshot" in output


def test_shape_sprint_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["shape-sprint"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Proposed Sprint Scope" in output


def test_retro_notes_mode(config, mock_jira, gatekeeper, audit_logger):
    mode_cls = MODE_REGISTRY["retro-notes"]
    executor = mode_cls(
        config=config,
        jira_client=mock_jira,
        gatekeeper=gatekeeper,
        audit_logger=audit_logger,
        apply=False,
    )
    output = executor.execute()
    assert "Retrospective Analysis" in output
    assert "Velocity & Delivery Metrics" in output
