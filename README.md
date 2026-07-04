# BudgetRigLab

A mostly-hands-off affiliate content site about **budget gaming setups & peripherals** — reviews, buying guides, and comparisons for gaming mice, keyboards, headsets, monitors, and controllers at real-person prices.

- **Stack:** Python 3.12 static site generator (stdlib + `markdown`), no JS frameworks, one CSS file, dark-friendly.
- **Hosting:** GitHub Pages (free), serving the `docs/` folder on `main`.
- **Revenue:** Amazon Associates affiliate links.
- **Automation:** a Windows scheduled task invokes Claude Code daily to write one new article, rebuild, and push.

> **Name/domain note:** "BudgetRigLab" was picked as a clean, brandable name. Domain availability was NOT verified (no web access during setup) — check `budgetriglab.com` before printing business cards. Everything (config, templates) makes the name easy to change in one place: `config.json`.

---

## Honest revenue expectations (read this first)

- **SEO traffic takes 3–6+ months.** New sites sit in a Google sandbox. Expect near-zero visitors for the first months regardless of content quality. This is normal, not failure.
- **AI-content sites must add real value.** Google's policies target mass-produced content that adds nothing. This site's articles are built around specific recommendations, honest tradeoffs, and comparison data — keep that standard for every generated article, and edit/fact-check what the automation produces. Pure autopilot with zero human review is how sites get deindexed.
- **Consistency beats bursts.** One decent article a day for six months outperforms 50 articles in week one and silence after.
- **Realistic math:** niche affiliate sites typically need ~10k monthly visitors to earn their first meaningful money ($100–300/mo at Amazon's 3–4% commission rates). Many sites never get there; the ones that do usually took a year. Treat this as a long-game side project, not income.
- **Amazon Associates has teeth:** you need **3 qualifying sales within 180 days** of joining or the account is closed (you can reapply). Don't sign up until the site is live and has some traffic.

---

## Folder layout

```
NicheSite/
├── config.json          Site name, URL, affiliate tag, settings
├── content/             Articles (markdown + frontmatter)
│   └── pages/           About + Affiliate Disclosure
├── templates/           base.html, article.html
├── static/              style.css (copied into docs/ at build)
├── docs/                BUILD OUTPUT — GitHub Pages serves this. Don't edit by hand.
└── scripts/
    ├── build.py                  Static site generator
    ├── new_article.ps1           Claude Code writes 1 article + deploys
    ├── deploy.ps1                Build + git commit + push
    ├── register_daily_task.ps1   One-time: register 10:00 AM daily task
    └── logs/                     Automation run logs
```

## Article format

```markdown
---
title: Best Budget Gaming Mice Under $30 in 2026
description: One-sentence meta description (~150 chars) for search results.
date: 2026-07-04
category: Mice
tags: mice, under-30, logitech, listicle
---

Article body in markdown. Tables, FAQ section, internal links to other
articles as relative links like [text](other-article-slug.html).
```

**Affiliate links** use the `aff:` scheme in markdown: `[Logitech G203](aff:B07YB8RJ4V)`. The build rewrites these to `https://www.amazon.com/dp/<ASIN>?tag=<your-tag>` with `rel="nofollow sponsored"` — the tag comes from `config.json`.

> **IMPORTANT — placeholder ASINs:** the ASINs in the initial 10 articles are plausible but unverified placeholders. Before (or shortly after) going live, click each product link and confirm it lands on the right product; fix any that don't. Search the content folder for `aff:` to list them all.

## Building locally

```powershell
# Once:
python -m pip install markdown

# Build (output -> docs/):
python scripts\build.py
```

Python 3.12 ARM64 is installed at `%LOCALAPPDATA%\Programs\Python\Python312-arm64\python.exe` if `python` isn't on PATH. Open `docs\index.html` in a browser to preview.

---

## One-time setup checklist (owner)

1. **Create a GitHub account** (if needed) and a new **public** repo, e.g. `budgetriglab`.
2. **Connect this folder to the repo** (the local repo and first commit already exist):
   ```powershell
   cd $HOME\OneDrive\Desktop\NicheSite
   git remote add origin https://github.com/YOURUSERNAME/budgetriglab.git
   git branch -M main
   git push -u origin main
   ```
3. **Enable GitHub Pages:** repo → Settings → Pages → "Deploy from a branch" → Branch: `main`, Folder: `/docs` → Save. The site appears at `https://YOURUSERNAME.github.io/budgetriglab/` within a couple of minutes.
4. **Update `config.json`:** set `site_url` to your real Pages URL (this fixes canonical URLs, the sitemap, and RSS), then run `scripts\deploy.ps1` once.
5. **Submit to Google:** [Google Search Console](https://search.google.com/search-console) → add property → verify (HTML tag method: add the tag to `templates/base.html` head) → submit `sitemap.xml`.
6. **Amazon Associates (after the site is live with content):** sign up at [affiliate-program.amazon.com](https://affiliate-program.amazon.com) using your live site URL. When approved, replace `"affiliate_tag": "CHANGEME-20"` in `config.json` with your real tag (looks like `yoursite-20`) and redeploy. Remember: **3 sales within 180 days** to keep the account.
7. **Verify placeholder ASINs** (see warning above).
8. **Optional — custom domain (~$12/yr):** buy `budgetriglab.com` (Namecheap/Cloudflare), add it in repo Settings → Pages → Custom domain, and set the registrar's DNS per GitHub's instructions (CNAME to `YOURUSERNAME.github.io`). A custom domain looks more trustworthy to both readers and Amazon.

## Daily automation

Once `scripts\deploy.ps1` works end-to-end (builds, commits, pushes, Pages updates):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_daily_task.ps1
```

This registers the Windows scheduled task **"NicheSite Daily Article"** at **10:00 AM daily**, which:

1. Invokes Claude Code headlessly (`claude -p ... --permission-mode acceptEdits`) to write one new 1200+ word article on an uncovered topic, matching the site's format and editorial standard;
2. Rebuilds the site;
3. Commits and pushes — GitHub Pages republishes automatically.

Logs land in `scripts\logs\`. Requirements: Claude Code CLI installed and authenticated for this Windows user, git credentials cached (first manual `git push` handles that), and the PC awake at 10 AM (the task runs at next boot if missed, via `StartWhenAvailable`).

**Recommended human-in-the-loop:** skim each new article within a day or two — check the ASINs, prices, and claims. Five minutes of review per article is the difference between a real site and AI slop.

## Editorial standard (used by the automation too)

Every article must have: 1200+ words; specific products with realistic street prices; **at least one honest downside per product**; a markdown comparison table; an FAQ section; 2–3 internal links to related articles; `aff:` links for products; a frontmatter block matching the format above. Article types rotate between "best X under $Y" listicles, head-to-head comparisons, and how-to guides.

## Maintenance

- **Change site name/URL/tag:** `config.json`, then rebuild.
- **Change design:** `static/style.css` and `templates/`, then rebuild.
- **Remove an article:** delete its `.md` from `content/`, rebuild, deploy.
- **Thin-content warning:** the build prints a warning for any article under 1000 words — fix or delete those.
