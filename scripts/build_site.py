#!/usr/bin/env python3
"""docs/ 以下のホームページを生成する。

  python3 scripts/build_site.py

読むもの:
  site.config.json  … サイト名・URL・各サービスのユーザー名
  articles/*.md     … Zenn 記事（published: true のものだけ）
  public/*.md       … Qiita 記事（private: false かつ ignorePublish: false のものだけ）

書くもの:
  docs/index.html
  docs/sitemap.xml

標準ライブラリだけで動く（PyYAML 不要）。
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


# --------------------------------------------------------------------------
# フロントマターの読み取り
# --------------------------------------------------------------------------

def split_front_matter(text: str) -> str:
    """先頭の --- ... --- を返す。無ければ空文字。"""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return "" if end == -1 else text[3:end]


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_front_matter(text: str) -> dict:
    """必要なスカラーキーだけを拾う素朴なパーサ。ネストは扱わない。"""
    data: dict[str, str] = {}
    for line in split_front_matter(text).splitlines():
        if not line or line.startswith("#") or line.startswith(" ") or line.startswith("-"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        data[key.strip()] = unquote(value)
    return data


def parse_topics(text: str) -> list[str]:
    """Zenn の topics: ["a", "b"] / Qiita の tags: の箇条書き、どちらも拾う。"""
    fm = split_front_matter(text)

    inline = re.search(r"^(?:topics|tags):\s*\[(.*)\]\s*$", fm, re.MULTILINE)
    if inline:
        return [unquote(t) for t in inline.group(1).split(",") if t.strip()]

    block = re.search(r"^(?:topics|tags):\s*$\n((?:\s+-\s+.*\n?)+)", fm, re.MULTILINE)
    if block:
        return [unquote(m) for m in re.findall(r"^\s+-\s+(.*)$", block.group(1), re.MULTILINE)]

    return []


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


# --------------------------------------------------------------------------
# 記事の収集
# --------------------------------------------------------------------------

def collect_zenn(cfg: dict) -> list[dict]:
    user = cfg.get("zenn_username", "").strip()
    articles = []
    for path in sorted((ROOT / "articles").glob("*.md")):
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        if not is_true(fm.get("published", "false")):
            continue
        articles.append({
            "title": fm.get("title", path.stem),
            "emoji": fm.get("emoji", "📝"),
            "topics": parse_topics(path.read_text(encoding="utf-8")),
            "date": "",
            "source": "Zenn",
            "url": f"https://zenn.dev/{user}/articles/{path.stem}" if user else "",
        })
    return articles


def collect_qiita(cfg: dict) -> list[dict]:
    user = cfg.get("qiita_username", "").strip()
    articles = []
    for path in sorted((ROOT / "public").glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm = parse_front_matter(raw)
        if is_true(fm.get("private", "false")) or is_true(fm.get("ignorePublish", "false")):
            continue
        item_id = fm.get("id", "")
        if item_id in ("", "null"):
            # まだ Qiita に投稿されていない下書き。リンク先が無いので載せない。
            continue
        # ユーザー名が未設定でも qiita.com/items/<id> は正規URLへ転送される。
        url = f"https://qiita.com/{user}/items/{item_id}" if user else f"https://qiita.com/items/{item_id}"
        articles.append({
            "title": fm.get("title", path.stem),
            "emoji": "📝",
            "topics": parse_topics(raw),
            "date": fm.get("updated_at", "")[:10],
            "source": "Qiita",
            "url": url,
        })
    return articles


def dedupe(articles: list[dict]) -> list[dict]:
    """同じ記事を Zenn と Qiita の両方に出している場合、片方だけ残す。"""
    seen: dict[str, dict] = {}
    for a in articles:
        key = re.sub(r"\s+", "", a["title"])
        kept = seen.get(key)
        # リンク先が判明している方を残す。両方あるなら先に来た方（Zenn）を優先。
        if kept is None or (not kept["url"] and a["url"]):
            seen[key] = a
    return list(seen.values())


# --------------------------------------------------------------------------
# HTML の組み立て
# --------------------------------------------------------------------------

def e(value: str) -> str:
    return html.escape(value, quote=True)


def render_article(a: dict) -> str:
    topics = "".join(f'<li class="topic">{e(t)}</li>' for t in a["topics"][:5])
    meta = f'<span class="source">{e(a["source"])}</span>'
    if a["date"]:
        meta += f'<time datetime="{e(a["date"])}">{e(a["date"])}</time>'

    title = f'<span class="emoji" aria-hidden="true">{e(a["emoji"])}</span>{e(a["title"])}'
    if a["url"]:
        title = f'<a href="{e(a["url"])}">{title}</a>'

    return f"""      <li class="article">
        <h3 class="article-title">{title}</h3>
        <p class="article-meta">{meta}</p>
        <ul class="topics">{topics}</ul>
      </li>"""


def render_links(cfg: dict) -> str:
    entries = [
        ("Zenn", f'https://zenn.dev/{cfg["zenn_username"]}' if cfg.get("zenn_username") else ""),
        ("Qiita", f'https://qiita.com/{cfg["qiita_username"]}' if cfg.get("qiita_username") else ""),
        ("GitHub", f'https://github.com/{cfg["github_username"]}' if cfg.get("github_username") else ""),
        ("X", f'https://x.com/{cfg["x_username"]}' if cfg.get("x_username") else ""),
    ]
    return "".join(
        f'<li><a href="{e(url)}" rel="me">{e(name)}</a></li>'
        for name, url in entries if url
    )


def render_index(cfg: dict, articles: list[dict]) -> str:
    base = cfg["base_url"].rstrip("/")
    profiles = [u for u in [
        f'https://zenn.dev/{cfg["zenn_username"]}' if cfg.get("zenn_username") else "",
        f'https://qiita.com/{cfg["qiita_username"]}' if cfg.get("qiita_username") else "",
        f'https://github.com/{cfg["github_username"]}' if cfg.get("github_username") else "",
    ] if u]

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "url": base + "/",
        "name": cfg["site_title"],
        "description": cfg["site_description"],
        "mainEntity": {
            "@type": "Person",
            "name": cfg["author_name"],
            "description": cfg["author_bio"],
            "url": base + "/",
            "sameAs": profiles,
        },
    }, ensure_ascii=False, indent=2)

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(cfg["site_title"])} | {e(cfg["site_tagline"])}</title>
<meta name="description" content="{e(cfg["site_description"])}">
<link rel="canonical" href="{e(base)}/">
<meta property="og:type" content="website">
<meta property="og:url" content="{e(base)}/">
<meta property="og:title" content="{e(cfg["site_title"])} | {e(cfg["site_tagline"])}">
<meta property="og:description" content="{e(cfg["site_description"])}">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="./style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='13' font-size='14'>📐</text></svg>">
<script type="application/ld+json">
{json_ld}
</script>
</head>
<body>
<header class="hero">
  <p class="eyebrow">{e(cfg["site_tagline"])}</p>
  <h1>{e(cfg["site_title"])}</h1>
  <p class="bio">{e(cfg["author_bio"])}</p>
  <ul class="links">{render_links(cfg)}</ul>
</header>

<main>
  <section aria-labelledby="articles-heading">
    <h2 id="articles-heading">記事</h2>
    <ul class="articles">
{chr(10).join(render_article(a) for a in articles)}
    </ul>
  </section>
</main>

<footer>
  <p>&copy; {datetime.now(timezone.utc).year} {e(cfg["author_name"])}</p>
  <p class="generated">このページは <code>scripts/build_site.py</code> で生成しています。</p>
</footer>
</body>
</html>
"""


def render_sitemap(cfg: dict) -> str:
    base = cfg["base_url"].rstrip("/")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base}/</loc>
    <lastmod>{today}</lastmod>
  </url>
</urlset>
"""


def render_robots(cfg: dict) -> str:
    base = cfg["base_url"].rstrip("/")
    return f"""User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
"""


def main() -> int:
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))

    articles = dedupe(collect_zenn(cfg) + collect_qiita(cfg))
    articles.sort(key=lambda a: a["date"], reverse=True)

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(render_index(cfg, articles), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(render_sitemap(cfg), encoding="utf-8")
    (DOCS / "robots.txt").write_text(render_robots(cfg), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")

    print(f"docs/index.html を生成しました（記事 {len(articles)} 本）")
    if not cfg.get("zenn_username"):
        print("注意: site.config.json の zenn_username が空です。Zenn 記事へのリンクが張れません。")
    if not cfg.get("qiita_username"):
        print("注意: site.config.json の qiita_username が空です。qiita.com/items/<id> の転送URLで代用しています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
