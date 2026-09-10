"""
utils/wiki_github.py
=====================
GitHub-committed storage for the Wiki/Know-How module (page 14).

Why GitHub and not local disk: Streamlit Community Cloud's filesystem is
ephemeral and resets on every redeploy/restart, so anything saved to
local files or SQLite disappears. Articles are instead stored as
markdown files (with YAML front-matter) inside this same repo, under
wiki/articles/, and read/written via the GitHub REST API's Contents
endpoint. This makes every submission a real, versioned git commit —
auditable, revertable, and durable across restarts.

Auth: expects a GITHUB_TOKEN in st.secrets, scoped to Contents:
read/write on this repo. No token = read-only browsing still works
(GitHub's Contents API allows unauthenticated reads on public repos,
rate-limited); only the "commit a new article" path requires it.

Pattern A note: this file does import streamlit (for st.secrets) and
therefore is NOT a pure domain engine module — it's a utility module,
same tier as utils/runner.py and utils/unit_converter.py, not a
domains/ engine file, so this does not violate the Pattern A rule that
domain engine files must have zero Streamlit imports.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
import streamlit as st
import yaml

GITHUB_API = "https://api.github.com"
REPO_OWNER = "paraschemix"
REPO_NAME = "Paras_ChemEnggsuite"
ARTICLES_DIR = "wiki/articles"
BRANCH = "main"


@dataclass
class WikiArticle:
    slug: str
    title: str
    domain: str
    author: str
    date: str
    tags: list[str]
    body: str
    sha: Optional[str] = None  # GitHub blob sha, needed to update an existing file


def _headers() -> dict:
    token = st.secrets.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _slugify(title: str) -> str:
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:80]


def _parse_markdown(raw: str) -> tuple[dict, str]:
    """Splits '---\\nyaml front-matter\\n---\\nbody' into (meta dict, body)."""
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].lstrip("\n")
            return meta, body
    return {}, raw


def _render_markdown(meta: dict, body: str) -> str:
    front_matter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
    return f"---\n{front_matter}---\n\n{body.strip()}\n"


@st.cache_data(ttl=120, show_spinner=False)
def list_articles(domain: Optional[str] = None) -> list[WikiArticle]:
    """Lists all articles under wiki/articles/. Cached 2 min so browsing
    the Wiki page doesn't hit the GitHub API on every rerun."""
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{ARTICLES_DIR}"
    resp = requests.get(url, headers=_headers(), params={"ref": BRANCH}, timeout=15)
    if resp.status_code == 404:
        return []  # folder doesn't exist yet — treated as "no articles", not an error
    resp.raise_for_status()

    articles: list[WikiArticle] = []
    for entry in resp.json():
        if not entry["name"].endswith(".md"):
            continue
        file_resp = requests.get(entry["url"], headers=_headers(), timeout=15)
        file_resp.raise_for_status()
        file_json = file_resp.json()
        raw = base64.b64decode(file_json["content"]).decode("utf-8")
        meta, body = _parse_markdown(raw)
        article = WikiArticle(
            slug=entry["name"].removesuffix(".md"),
            title=meta.get("title", entry["name"]),
            domain=meta.get("domain", "General"),
            author=meta.get("author", "Unknown"),
            date=meta.get("date", ""),
            tags=meta.get("tags", []),
            body=body,
            sha=file_json["sha"],
        )
        if domain is None or article.domain == domain:
            articles.append(article)

    articles.sort(key=lambda a: a.date, reverse=True)
    return articles


def read_article(slug: str) -> Optional[WikiArticle]:
    for article in list_articles():
        if article.slug == slug:
            return article
    return None


def commit_article(
    title: str,
    domain: str,
    author: str,
    tags: list[str],
    body: str,
    edit_slug: Optional[str] = None,
) -> tuple[bool, str]:
    """Creates a new article, or updates an existing one if edit_slug is
    given. Returns (success, message). Requires GITHUB_TOKEN with write
    access — caller (the page) is responsible for checking the shared
    WIKI_EDIT_TOKEN gate before calling this."""
    token = st.secrets.get("GITHUB_TOKEN")
    if not token:
        return False, "GITHUB_TOKEN not configured in Streamlit Secrets — cannot save."

    slug = edit_slug or _slugify(title)
    if not slug:
        return False, "Could not derive a valid slug from the title — please rephrase it."

    meta = {
        "title": title,
        "domain": domain,
        "author": author or "Anonymous",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "tags": tags,
    }
    content = _render_markdown(meta, body)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")

    path = f"{ARTICLES_DIR}/{slug}.md"
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}"

    # If updating, we need the existing file's sha; look it up fresh
    # (not from cache) so a stale sha never causes a silent overwrite
    # conflict.
    sha = None
    existing = requests.get(url, headers=_headers(), params={"ref": BRANCH}, timeout=15)
    if existing.status_code == 200:
        sha = existing.json()["sha"]

    commit_message = f"Wiki: {'update' if sha else 'add'} article '{title}'"
    payload = {
        "message": commit_message,
        "content": encoded,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=_headers(), json=payload, timeout=15)
    if resp.status_code in (200, 201):
        list_articles.clear()  # invalidate cache so the new/edited article shows immediately
        return True, f"Saved '{title}' to {path} (commit {resp.json()['commit']['sha'][:7]})."
    return False, f"GitHub API error {resp.status_code}: {resp.text[:300]}"
