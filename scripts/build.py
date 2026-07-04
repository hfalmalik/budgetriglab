#!/usr/bin/env python3
"""
BudgetRigLab static site generator.

Stdlib + the `markdown` package only. Renders content/*.md into docs/
(GitHub Pages serves from docs/ on the main branch).

Features:
  - Frontmatter parsing (title, description, date, category, tags)
  - aff: link rewriting -> Amazon affiliate URLs using config.json affiliate_tag
  - Index page grouped by category, per-category pages
  - About / Affiliate Disclosure pages from content/pages/
  - sitemap.xml, robots.txt, rss.xml
  - Related-article internal links (shared category/tags)
  - FTC/Amazon affiliate disclosure on every page (baked into base template)

Usage:  python scripts/build.py
"""

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency. Run:  python -m pip install markdown")

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
PAGES = CONTENT / "pages"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"

MD_EXTENSIONS = ["tables", "fenced_code", "sane_lists", "smarty"]

AFF_RE = re.compile(r'href="aff:([A-Za-z0-9]+)"')


# ---------------------------------------------------------------- helpers

def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def load_template(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(template, **ctx):
    """Tiny mustache-ish renderer: replaces {{key}} tokens."""
    out = template
    for key, val in ctx.items():
        out = out.replace("{{" + key + "}}", str(val))
    return out


def parse_frontmatter(text, path):
    """Returns (meta dict, body str). Frontmatter is --- delimited key: value."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    meta[key.strip().lower()] = val.strip().strip('"')
            body = parts[2].lstrip("\n")
    for required in ("title", "description", "date"):
        if required not in meta:
            sys.exit(f"ERROR: {path.name} is missing required frontmatter field '{required}'")
    return meta, body


def slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "page"


def rewrite_affiliate_links(html, tag):
    """aff:ASIN hrefs -> tagged Amazon links, opened in a new tab, rel per Google/FTC."""
    def repl(m):
        asin = m.group(1)
        return (f'href="https://www.amazon.com/dp/{asin}?tag={tag}" '
                f'rel="nofollow sponsored noopener" target="_blank"')
    return AFF_RE.sub(repl, html)


def md_to_html(body, cfg):
    html = markdown.markdown(body, extensions=MD_EXTENSIONS)
    return rewrite_affiliate_links(html, cfg["affiliate_tag"])


def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")


def rfc822(dt):
    return dt.replace(tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


# ---------------------------------------------------------------- build steps

def collect_articles(cfg):
    articles = []
    for path in sorted(CONTENT.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        slug = slugify(path.stem)
        tags = [t.strip().lower() for t in meta.get("tags", "").split(",") if t.strip()]
        articles.append({
            "slug": slug,
            "url": f"{slug}.html",
            "title": meta["title"],
            "description": meta["description"],
            "date": parse_date(meta["date"]),
            "date_str": meta["date"],
            "category": meta.get("category", "Uncategorized"),
            "tags": tags,
            "html": md_to_html(body, cfg),
            "words": len(body.split()),
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


def related_articles(article, articles, limit=3):
    scored = []
    for other in articles:
        if other["slug"] == article["slug"]:
            continue
        score = len(set(article["tags"]) & set(other["tags"]))
        if other["category"] == article["category"]:
            score += 2
        if score:
            scored.append((score, other))
    scored.sort(key=lambda x: (-x[0], x[1]["date"]), reverse=False)
    return [o for _, o in scored[:limit]]


def article_card(a):
    return (
        '<article class="card">'
        f'<p class="card-meta">{escape(a["category"])} &middot; '
        f'<time datetime="{a["date_str"]}">{a["date"].strftime("%b %d, %Y")}</time></p>'
        f'<h3><a href="{a["url"]}">{escape(a["title"])}</a></h3>'
        f'<p>{escape(a["description"])}</p>'
        "</article>"
    )


def build_page(base, cfg, *, title, description, canonical, content, og_type="website"):
    return render(
        base,
        site_name=cfg["site_name"],
        site_tagline=cfg["site_tagline"],
        site_url=cfg["site_url"],
        page_title=escape(title),
        meta_description=escape(description),
        canonical_url=canonical,
        og_type=og_type,
        content=content,
        year=datetime.now().year,
    )


def main():
    cfg = load_config()
    out = ROOT / cfg.get("output_dir", "docs")
    site_url = cfg["site_url"].rstrip("/")

    if cfg["affiliate_tag"].startswith("CHANGEME"):
        print("NOTE: affiliate_tag in config.json is still the placeholder "
              "'CHANGEME-20'. Replace it after Amazon Associates approval.")

    # Clean output dir (keep the dir itself so git/OneDrive stay calm)
    out.mkdir(exist_ok=True)
    for item in out.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    base = load_template("base.html")
    article_tpl = load_template("article.html")

    articles = collect_articles(cfg)
    if not articles:
        sys.exit("ERROR: no articles found in content/")

    # --- article pages
    for a in articles:
        rel = related_articles(a, articles)
        related_html = ""
        if rel:
            items = "".join(
                f'<li><a href="{r["url"]}">{escape(r["title"])}</a></li>' for r in rel
            )
            related_html = (f'<aside class="related"><h2>Related reads</h2>'
                            f"<ul>{items}</ul></aside>")
        content = render(
            article_tpl,
            title=escape(a["title"]),
            category=escape(a["category"]),
            category_url=f'category-{slugify(a["category"])}.html',
            date_str=a["date_str"],
            date_human=a["date"].strftime("%B %d, %Y"),
            body=a["html"],
            related=related_html,
        )
        page = build_page(base, cfg, title=f'{a["title"]} — {cfg["site_name"]}',
                          description=a["description"],
                          canonical=f'{site_url}/{a["url"]}',
                          content=content, og_type="article")
        (out / a["url"]).write_text(page, encoding="utf-8")

    # --- categories
    categories = {}
    for a in articles:
        categories.setdefault(a["category"], []).append(a)

    for cat, items in sorted(categories.items()):
        cat_slug = slugify(cat)
        cards = "".join(article_card(a) for a in items)
        content = (f'<h1>{escape(cat)}</h1>'
                   f'<p class="lede">{len(items)} article(s) in this category.</p>'
                   f'<div class="cards">{cards}</div>')
        page = build_page(base, cfg, title=f'{cat} — {cfg["site_name"]}',
                          description=f'All {cfg["site_name"]} articles about {cat.lower()}.',
                          canonical=f"{site_url}/category-{cat_slug}.html",
                          content=content)
        (out / f"category-{cat_slug}.html").write_text(page, encoding="utf-8")

    # --- index
    cat_nav = " ".join(
        f'<a class="pill" href="category-{slugify(c)}.html">{escape(c)} '
        f"({len(items)})</a>"
        for c, items in sorted(categories.items())
    )
    latest = "".join(article_card(a) for a in articles)
    index_content = (
        f'<section class="hero"><h1>{escape(cfg["site_name"])}</h1>'
        f'<p class="lede">{escape(cfg["site_tagline"])}. Every pick here costs less than '
        f"one AAA game per year of use, and we tell you what you give up at each price.</p>"
        f'<nav class="pills" aria-label="Categories">{cat_nav}</nav></section>'
        f"<h2>Latest articles</h2>"
        f'<div class="cards">{latest}</div>'
    )
    page = build_page(base, cfg, title=f'{cfg["site_name"]} — {cfg["site_tagline"]}',
                      description=cfg["site_description"],
                      canonical=f"{site_url}/", content=index_content)
    (out / "index.html").write_text(page, encoding="utf-8")

    # --- static pages (about, affiliate disclosure)
    static_pages = []
    for path in sorted(PAGES.glob("*.md")) if PAGES.exists() else []:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        slug = slugify(path.stem)
        html = md_to_html(body, cfg)
        page = build_page(base, cfg, title=f'{meta["title"]} — {cfg["site_name"]}',
                          description=meta["description"],
                          canonical=f"{site_url}/{slug}.html",
                          content=f'<article class="prose">{html}</article>')
        (out / f"{slug}.html").write_text(page, encoding="utf-8")
        static_pages.append({"url": f"{slug}.html", "date_str": meta["date"]})

    # --- static assets
    if STATIC.exists():
        for item in STATIC.iterdir():
            if item.is_file():
                shutil.copy2(item, out / item.name)

    # --- robots.txt
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n", encoding="utf-8")

    # --- .nojekyll (skip Jekyll processing on GitHub Pages)
    (out / ".nojekyll").write_text("", encoding="utf-8")

    # --- sitemap.xml
    urls = [f"{site_url}/"]
    urls += [f"{site_url}/{a['url']}" for a in articles]
    urls += [f"{site_url}/category-{slugify(c)}.html" for c in categories]
    urls += [f"{site_url}/{p['url']}" for p in static_pages]
    today = datetime.now().strftime("%Y-%m-%d")
    entries = "".join(
        f"  <url><loc>{escape(u)}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}</urlset>\n", encoding="utf-8")

    # --- rss.xml
    items = ""
    for a in articles[: cfg.get("posts_per_feed", 20)]:
        items += (
            "  <item>\n"
            f"    <title>{escape(a['title'])}</title>\n"
            f"    <link>{site_url}/{a['url']}</link>\n"
            f"    <guid>{site_url}/{a['url']}</guid>\n"
            f"    <pubDate>{rfc822(a['date'])}</pubDate>\n"
            f"    <description>{escape(a['description'])}</description>\n"
            "  </item>\n"
        )
    (out / "rss.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        f"  <title>{escape(cfg['site_name'])}</title>\n"
        f"  <link>{site_url}/</link>\n"
        f"  <description>{escape(cfg['site_description'])}</description>\n"
        f"  <lastBuildDate>{rfc822(datetime.now())}</lastBuildDate>\n"
        f"{items}</channel></rss>\n", encoding="utf-8")

    # --- summary
    thin = [a for a in articles if a["words"] < 1000]
    print(f"Built {len(articles)} articles, {len(categories)} categories, "
          f"{len(static_pages)} static pages -> {out}")
    if thin:
        print("WARNING: articles under 1000 words (thin content hurts SEO):")
        for a in thin:
            print(f"  - {a['slug']} ({a['words']} words)")


if __name__ == "__main__":
    main()
