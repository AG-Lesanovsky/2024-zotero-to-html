#!/usr/bin/env python3
"""
Full-text search on arXiv via search.arxiv.org, then enrich results with metadata
from the official arXiv API and save to CSV.

Usage:
  python arxiv_fulltext_search.py \
    --query "https://search.arxiv.org/?in=&query=465199066" \
    --out results.csv [--render]

Notes:
- This script scrapes search.arxiv.org to get arXiv IDs for FULL-TEXT matches.
- Some results are loaded dynamically via JavaScript; if you get empty results, add `--render`.
- It then calls the official arXiv Atom API to fetch rich metadata for those IDs.
- Affiliations are included if present in the Atom feed (some entries omit them).
- Be mindful of arXiv's rate limits; the script sleeps politely between requests.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from typing import Dict, Iterable, List, Optional, Set

import requests
from bs4 import BeautifulSoup
import feedparser

# Optional JS rendering (enabled with --render)
try:
    from playwright.sync_api import sync_playwright  # type: ignore

    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False

SEARCH_BASE = "https://search.arxiv.org/"
ARXIV_API = "http://export.arxiv.org/api/query"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ARXIV_ID_RE = re.compile(
    r"arxiv\.org/(?:abs|pdf)/((?:\d{4}\.\d{4,5})|(?:[a-z\-]+/\d{7}))",
    re.I,
)


def http_get(url: str, params: Optional[dict] = None, *, retries: int = 3, timeout: int = 30) -> requests.Response:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            if attempt < retries:
                time.sleep(1.5 * attempt)
            else:
                raise
    raise last_exc  # type: ignore[misc]


def extract_ids_from_search_html(html: str) -> Set[str]:
    soup = BeautifulSoup(html, "html.parser")
    ids: Set[str] = set()
    for a in soup.find_all("a", href=True):
        m = ARXIV_ID_RE.search(a["href"])
        if m:
            ids.add(m.group(1))
    return ids


def find_next_page_url(html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = [
        a for a in soup.find_all("a", href=True)
        if a.get_text(strip=True).lower() in {"next", "next >", ">", "next page"}
           or ("next" in (a.get("rel") or []))
    ]
    for a in candidates:
        href = a["href"]
        if href.startswith("http"):
            return href
        else:
            return requests.compat.urljoin(SEARCH_BASE, href)
    for a in soup.find_all("a", href=True, rel=True):
        rels = {r.lower() for r in a.get("rel", [])}
        if "next" in rels:
            href = a["href"]
            if href.startswith("http"):
                return href
            else:
                return requests.compat.urljoin(SEARCH_BASE, href)
    return None


def search_fulltext_collect_ids(query: str, max_pages: int = 10, sleep_sec: float = 1.0) -> List[str]:
    params = {"query": query}
    url = SEARCH_BASE
    seen_ids: Set[str] = set()
    pages_fetched = 0
    while url and pages_fetched < max_pages:
        resp = http_get(url, params=params if pages_fetched == 0 else None)
        html = resp.text
        new_ids = extract_ids_from_search_html(html)
        seen_ids.update(new_ids)
        pages_fetched += 1
        next_url = find_next_page_url(html)
        if not next_url:
            break
        url = next_url
        params = None
        time.sleep(sleep_sec)
    return sorted(seen_ids)


def search_fulltext_collect_ids_render(query: str, max_pages: int = 10, sleep_sec: float = 1.0) -> List[str]:
    if not HAS_PLAYWRIGHT:
        raise RuntimeError("--render requested but Playwright is not installed.")
    from urllib.parse import quote
    ids: Set[str] = set()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=USER_AGENT)
        url = SEARCH_BASE + f"?query={quote(query)}"
        pages_fetched = 0
        while url and pages_fetched < max_pages:
            page.goto(url, wait_until="networkidle")
            html = page.content()
            ids.update(extract_ids_from_search_html(html))
            next_href = None
            try:
                next_link = page.locator('a:has-text("Next")')
                if next_link.count() > 0:
                    next_href = next_link.first.get_attribute("href")
            except Exception:
                pass
            if not next_href:
                try:
                    next_href = page.eval_on_selector("link[rel=next]", "el => el && el.href")
                except Exception:
                    next_href = None
            if not next_href:
                break
            url = next_href
            pages_fetched += 1
            time.sleep(sleep_sec)
        browser.close()
    return sorted(ids)


def chunks(iterable: List[str], n: int) -> Iterable[List[str]]:
    for i in range(0, len(iterable), n):
        yield iterable[i: i + n]


def fetch_metadata_for_ids(arxiv_ids: List[str], *, batch_size: int = 50, sleep_sec: float = 3.0) -> List[Dict]:
    results: List[Dict] = []
    for batch in chunks(arxiv_ids, batch_size):
        params = {"id_list": ",".join(batch)}
        resp = http_get(ARXIV_API, params=params)
        feed = feedparser.parse(resp.text)
        for entry in feed.entries:
            entry_id = entry.get("id", "")
            arxiv_id = None
            doi = entry.get("arxiv_doi") if "arxiv_doi" in entry else None
            m = re.search(r"arxiv\.org/(?:abs|pdf)/([\w\.-/]+)", entry_id)
            if m:
                arxiv_id = m.group(1)
            pdf_url = None
            abs_url = None
            for link in entry.get("links", []):
                href = link.get("href")
                if not href:
                    continue
                if link.get("type") == "application/pdf" or href.endswith(".pdf"):
                    pdf_url = href
                if "arxiv.org/abs/" in href:
                    abs_url = href
            authors = []
            for a in entry.get("authors", []):
                name = a.get("name") if isinstance(a, dict) else str(a)
                aff = None
                if hasattr(a, "get"):
                    aff = a.get("affiliation") or a.get("arxiv_affiliation")
                if not aff:
                    aff = getattr(a, "arxiv_affiliation", None)
                authors.append({"name": name, "affiliation": aff})
            primary_cat = None
            if "arxiv_primary_category" in entry:
                primary_cat = entry.arxiv_primary_category.get("term")
            categories = [t.get("term") for t in entry.get("tags", []) if t.get("term")]
            comment = getattr(entry, "arxiv_comment", None)
            journal_ref = getattr(entry, "arxiv_journal_ref", None)
            result = {
                "arxiv_id": arxiv_id,
                "title": entry.get("title"),
                "abstract": entry.get("summary"),
                "published": entry.get("published"),
                "updated": entry.get("updated"),
                "authors": authors,
                "primary_category": primary_cat,
                "categories": categories,
                "doi": doi,
                "pdf_url": pdf_url,
                "abs_url": abs_url,
                "comment": comment,
                "journal_ref": journal_ref,
            }
            results.append(result)
        time.sleep(sleep_sec)
    return results


def save_csv(data: List[Dict], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        header = [
            "arxiv_id", "title", "abstract", "published", "updated",
            "authors", "primary_category", "categories", "doi", "pdf_url",
            "abs_url", "comment", "journal_ref"
        ]
        writer.writerow(header)
        for item in data:
            authors_str = "; ".join(
                [f"{a['name']} ({a['affiliation']})" if a['affiliation'] else a['name'] for a in item["authors"]]
            )
            categories_str = ", ".join(item["categories"])
            row = [
                item["arxiv_id"], item["title"], item["abstract"], item["published"], item["updated"],
                authors_str, item["primary_category"], categories_str, item["doi"], item["pdf_url"],
                item["abs_url"], item["comment"], item["journal_ref"]
            ]
            writer.writerow(row)


def run(query: str, out_path: str, max_pages: int = 10, render: bool = False) -> None:
    ids = search_fulltext_collect_ids_render(query, max_pages=max_pages) if render else search_fulltext_collect_ids(
        query, max_pages=max_pages)
    meta = fetch_metadata_for_ids(ids)
    save_csv(meta, out_path)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Full-text search arXiv, export metadata to CSV.")
    parser.add_argument("--query", required=True, help="Full-text search query (e.g., a URL or phrase).")
    parser.add_argument("--out", default="arxiv_fulltext_results.csv", help="Output CSV file path.")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to crawl from search.arxiv.org.")
    parser.add_argument("--render", action="store_true",
                        help="Use headless browser rendering (Playwright) for dynamic pages.")
    args = parser.parse_args(argv)
    try:
        run(args.query, args.out, max_pages=args.max_pages, render=args.render)
        print(f"Saved results to {args.out}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
