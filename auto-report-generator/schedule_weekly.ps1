# Register a Windows Scheduled Task so the report regenerates itself every
# Monday at 8 AM — this is the "automation". Run this script ONCE.
#
#   powershell -ExecutionPolicy Bypass -File .\schedule_weekly.ps1
#
$python = (Get-Command python).Source
$script = Join-Path $PSScriptRoot "run_report.py"

$action  = New-ScheduledTaskAction  -Execute $python -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am

Register-ScheduledTask -TaskName "AutoAnalyst Weekly Report" -Action $action -Trigger $trigger `
    -Description "Auto-generate the weekly sales report" -Force

Write-Host "Scheduled: the report will regenerate every Monday at 8 AM."
Write-Host "Remove it later with:  Unregister-ScheduledTask -TaskName 'AutoAnalyst Weekly Report'"
