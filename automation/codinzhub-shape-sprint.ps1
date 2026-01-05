<#
.SYNOPSIS
  CodinzHub Shape Sprint PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "shape-sprint" @args
