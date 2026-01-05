<#
.SYNOPSIS
  CodinzHub Triage Queue PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "triage-queue" @args
