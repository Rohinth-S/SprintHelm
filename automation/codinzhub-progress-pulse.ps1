<#
.SYNOPSIS
  CodinzHub Progress Pulse PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "progress-pulse" @args
