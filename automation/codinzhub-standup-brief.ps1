<#
.SYNOPSIS
  CodinzHub Standup Brief PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "standup-brief" @args
