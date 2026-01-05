<#
.SYNOPSIS
  CodinzHub Inspect Sprint PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "inspect-sprint" @args
