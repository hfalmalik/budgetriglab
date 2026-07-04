# register_daily_task.ps1 — registers the Windows scheduled task "NicheSite Daily Article".
# RUN THIS ONCE, YOURSELF, after deploy.ps1 works end-to-end (repo + remote + Pages enabled).
# Run from an elevated or normal PowerShell:  powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $PSScriptRoot "new_article.ps1"
$TaskName = "NicheSite Daily Article"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`"" `
    -WorkingDirectory $Root

$Trigger = New-ScheduledTaskTrigger -Daily -At 10:00AM

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed existing task '$TaskName'."
}

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings `
    -Description "Generates one new BudgetRigLab article via Claude Code and deploys to GitHub Pages." | Out-Null

Write-Host "Registered task '$TaskName' - runs daily at 10:00 AM."
Write-Host "Test it now with:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Logs land in:      $Root\scripts\logs\"
