<#
.SYNOPSIS
  CodinzHub Suggest Owner PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "suggest-owner" @args
