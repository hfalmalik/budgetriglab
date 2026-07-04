# new_article.ps1 — generates ONE new article via Claude Code (headless), rebuilds, deploys.
# Run manually or via the "NicheSite Daily Article" scheduled task (see register_daily_task.ps1).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot   # NicheSite folder
Set-Location $Root

$LogDir = Join-Path $Root "scripts\logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$Log = Join-Path $LogDir ("article-" + (Get-Date -Format "yyyy-MM-dd-HHmm") + ".log")

"[$(Get-Date)] Starting article generation..." | Tee-Object -FilePath $Log

$CountBefore = (Get-ChildItem "$Root\content\*.md").Count

$Prompt = @"
You are the content engine for the affiliate site at $Root (BudgetRigLab - budget gaming setups and peripherals).
1. Read README.md for the editorial standard, and list the existing article titles/topics in content/ (read the frontmatter of each .md file) so you do not repeat a topic.
2. Write ONE new SEO article of 1200+ words on a budget gaming gear topic NOT yet covered. Match the exact frontmatter format of existing files (title, description, date [today], category, tags). Requirements: specific product recommendations with realistic specs and street prices, at least one honest downside per product, a markdown comparison table, an FAQ section, 2-3 internal links to related existing articles (relative .html links), and product links in the form [Product Name](aff:ASIN) using plausible ASINs (note: owner verifies ASINs). Rotate article types: listicle, head-to-head comparison, or how-to guide - pick whichever is least represented.
3. Save it to content/ with a kebab-case filename matching the slug.
4. Run: python scripts/build.py  (use the python on PATH, or $env:LOCALAPPDATA\Programs\Python\Python312-arm64\python.exe if not found) and confirm it succeeds.
"@

# Invoke Claude Code headlessly
claude -p $Prompt --permission-mode acceptEdits 2>&1 | Tee-Object -FilePath $Log -Append

$CountAfter = (Get-ChildItem "$Root\content\*.md").Count
if ($CountAfter -le $CountBefore) {
    "[$(Get-Date)] WARNING: no new article file detected. Check the log: $Log" | Tee-Object -FilePath $Log -Append
    exit 1
}

"[$(Get-Date)] New article created ($CountBefore -> $CountAfter). Deploying..." | Tee-Object -FilePath $Log -Append

# Build + commit + push
& (Join-Path $PSScriptRoot "deploy.ps1") 2>&1 | Tee-Object -FilePath $Log -Append

"[$(Get-Date)] Done." | Tee-Object -FilePath $Log -Append
