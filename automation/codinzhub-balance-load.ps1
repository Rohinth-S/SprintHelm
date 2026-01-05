<#
.SYNOPSIS
  CodinzHub Balance Load PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& "$scriptDir\codinzhub-run-sprint-guardian.ps1" -Mode "balance-load" @args
