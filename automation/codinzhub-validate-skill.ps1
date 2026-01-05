<#
.SYNOPSIS
  CodinzHub Skill Configuration Validator PowerShell Wrapper
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptDir\codinzhub-validate-skill.py"
