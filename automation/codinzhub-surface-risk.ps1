<#
.SYNOPSIS
  CodinzHub Surface Risk PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "surface-risk" @args
