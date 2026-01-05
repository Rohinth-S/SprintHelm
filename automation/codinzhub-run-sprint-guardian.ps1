<#
.SYNOPSIS
  CodinzHub Sprint Guardian - Master Orchestration PowerShell Script
.DESCRIPTION
  Runs the Sprint Guardian Python engine or Codex execution with approval checks.
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true)]
    [ValidateSet("shape-sprint", "triage-queue", "suggest-owner", "balance-load", "inspect-sprint", "surface-risk", "progress-pulse", "standup-brief", "retro-notes")]
    [string]$Mode,

    [switch]$Apply,
    [string]$ApprovedBy = "",
    [string]$ApprovalNote = "",
    [string]$BoardId = "",
    [string]$ProjectKey = "",
    [string]$SprintId = "",
    [string]$SprintName = "",
    [string]$StartDate = "",
    [string]$EndDate = "",
    [string]$IssueKeys = "",
    [string]$Jql = "",
    [string]$OutputFile = "",
    [string]$TeamMap = "",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Usage:
  .\codinzhub-run-sprint-guardian.ps1 -Mode <MODE> [options]

Modes:
  shape-sprint, triage-queue, suggest-owner, balance-load,
  inspect-sprint, surface-risk, progress-pulse, standup-brief, retro-notes

Options:
  -Apply                Allow Jira mutations. Default is dry-run.
  -ApprovedBy <NAME>    Required for mutations that modify assignees.
  -ApprovalNote <TEXT>  Optional audit log note.
  -IssueKeys <KEYS>     Comma-separated Jira issue keys.
"@
    exit 0
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

$argsList = @("-m", "sprint_guardian", "--mode", $Mode)

if ($Apply) { $argsList += "--apply" }
if ($ApprovedBy) { $argsList += @("--approved-by", $ApprovedBy) }
if ($ApprovalNote) { $argsList += @("--approval-note", $ApprovalNote) }
if ($BoardId) { $argsList += @("--board-id", $BoardId) }
if ($ProjectKey) { $argsList += @("--project-key", $ProjectKey) }
if ($SprintId) { $argsList += @("--sprint-id", $SprintId) }
if ($SprintName) { $argsList += @("--sprint-name", $SprintName) }
if ($StartDate) { $argsList += @("--start-date", $StartDate) }
if ($EndDate) { $argsList += @("--end-date", $EndDate) }
if ($IssueKeys) { $argsList += @("--issue-keys", $IssueKeys) }
if ($Jql) { $argsList += @("--jql", $Jql) }
if ($OutputFile) { $argsList += @("--output-file", $OutputFile) }
if ($TeamMap) { $argsList += @("--team-map", $TeamMap) }

Push-Location $rootDir
try {
    python @argsList
} finally {
    Pop-Location
}
