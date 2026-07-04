# deploy.ps1 — build the site into docs/ then commit and push to GitHub.
# GitHub Pages (configured to serve /docs on main) publishes automatically after push.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# Locate Python (PATH first, then the known 3.12 ARM64 install)
$Python = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $Candidate = "$env:LOCALAPPDATA\Programs\Python\Python312-arm64\python.exe"
    if (Test-Path $Candidate) { $Python = $Candidate }
    else { throw "Python not found. Install Python 3.12 and 'pip install markdown'." }
}

Write-Host "Building site..."
& $Python "$Root\scripts\build.py"
if ($LASTEXITCODE -ne 0) { throw "Build failed - aborting deploy." }

Write-Host "Committing and pushing..."
git add -A
$Pending = git status --porcelain
if (-not $Pending) {
    Write-Host "Nothing to commit - site already up to date."
    exit 0
}
git commit -m ("Site update " + (Get-Date -Format "yyyy-MM-dd HH:mm"))

# Push only if a remote is configured (README explains one-time remote setup)
$Remote = git remote
if ($Remote) {
    git push
    Write-Host "Pushed. GitHub Pages will update in ~1 minute."
} else {
    Write-Host "NOTE: no git remote configured yet. Committed locally only."
    Write-Host "See README.md 'One-time setup' to create the GitHub repo and add the remote."
}
