<#
.SYNOPSIS
  CodinzHub Retro Notes PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "retro-notes" @args
