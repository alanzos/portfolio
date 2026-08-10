#!/usr/bin/env python3
"""Create a Buttondown draft (optionally send) from a portfolio article.

Auth: ~/.config/portfolio/buttondown.env (BUTTONDOWN_API_KEY), or env vars.

Examples:
  scripts/newsletter_from_article.py articles/2026-08-10-disease-independent-clocks
  scripts/newsletter_from_article.py articles/2026-08-10-disease-independent-clocks --dry-run
  scripts/newsletter_from_article.py articles/2026-08-10-disease-independent-clocks --send
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = Path.home() / ".config" / "portfolio" / "buttondown.env"
DEFAULT_API_BASE = "https://api.buttondown.com/v1"
DEFAULT_SITE_BASE = "https://andreslanzos.quarto.pub/portfolio"
METADATA_SOURCE = "portfolio"
METADATA_ARTICLE_KEY = "portfolio_article"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


def resolve_article_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if path.is_dir():
        path = path / "index.qmd"
    if not path.is_file():
        raise SystemExit(f"Article not found: {raw}")
    try:
        path.relative_to(REPO_ROOT / "articles")
    except ValueError as exc:
        raise SystemExit(f"Article must live under articles/: {path}") from exc
    return path


def article_slug(article_path: Path) -> str:
    return article_path.parent.name


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise SystemExit("Article is missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise SystemExit("Article frontmatter is not closed")
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        meta[key] = value
    return meta, body


def extract_tldr(body: str) -> str | None:
    match = re.search(
        r"::: \{\.tldr\}\s*(.*?)\s*:::",
        body,
        flags=re.DOTALL,
    )
    if not match:
        return None
    tldr = match.group(1).strip()
    tldr = re.sub(r"^\*\*TLDR\.\*\*\s*", "", tldr)
    tldr = re.sub(r"\n+", " ", tldr)
    return tldr.strip() or None


def absolute_url(site_base: str, slug: str, relative: str | None = None) -> str:
    base = f"{site_base.rstrip('/')}/articles/{slug}/"
    if not relative:
        return base
    return urllib.parse.urljoin(base, relative.lstrip("/"))


def build_email_body(
    *,
    title: str,
    description: str,
    tldr: str | None,
    article_url: str,
) -> str:
    parts = [
        "<!-- buttondown-editor-mode: plaintext -->",
        "",
        "New article on the portfolio:",
        "",
        f"# {title}",
        "",
    ]
    if description:
        parts.extend([description, ""])
    if tldr:
        parts.extend([f"**TLDR.** {tldr}", ""])
    parts.extend(
        [
            f"[Read the full article →]({article_url})",
            "",
            "—",
            "",
            "You’re receiving this because you subscribed via the portfolio Articles page.",
        ]
    )
    return "\n".join(parts)


def api_request(
    method: str,
    path: str,
    *,
    api_base: str,
    api_key: str,
    payload: dict | None = None,
) -> dict | list | None:
    url = f"{api_base.rstrip('/')}/{path.lstrip('/')}"
    data = None
    headers = {
        "Authorization": f"Token {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Buttondown API {method} {path} failed ({exc.code}): {detail}") from exc


def list_emails(*, api_base: str, api_key: str) -> list[dict]:
    emails: list[dict] = []
    page = 1
    while True:
        data = api_request(
            "GET",
            f"emails?page={page}&page_size=50",
            api_base=api_base,
            api_key=api_key,
        )
        if not isinstance(data, dict):
            break
        results = data.get("results") or []
        emails.extend(results)
        if not data.get("next"):
            break
        page += 1
    return emails


def find_existing(emails: list[dict], slug: str) -> dict | None:
    for email in emails:
        meta = email.get("metadata") or {}
        if meta.get(METADATA_ARTICLE_KEY) == slug and meta.get("source") == METADATA_SOURCE:
            return email
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Buttondown newsletter draft from a portfolio article."
    )
    parser.add_argument(
        "article",
        help="Article folder or index.qmd under articles/",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Publish/send immediately after creating the draft (default: draft only).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the payload without calling the API.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create even if an email already exists for this article slug.",
    )
    parser.add_argument(
        "--site-base",
        default=os.environ.get("PORTFOLIO_SITE_BASE", DEFAULT_SITE_BASE),
        help=f"Public site base URL (default: {DEFAULT_SITE_BASE})",
    )
    args = parser.parse_args()

    load_env_file(Path(os.environ.get("BUTTONDOWN_ENV_FILE", DEFAULT_ENV_FILE)))
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    api_base = os.environ.get("BUTTONDOWN_API_BASE", DEFAULT_API_BASE).strip()
    if not args.dry_run and not api_key:
        raise SystemExit(
            "Missing BUTTONDOWN_API_KEY. Set it or add ~/.config/portfolio/buttondown.env"
        )

    article_path = resolve_article_path(args.article)
    slug = article_slug(article_path)
    text = article_path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    title = meta.get("title", "").strip()
    if not title:
        raise SystemExit("Article frontmatter is missing title")
    description = meta.get("description", "").strip()
    image = meta.get("image", "").strip() or None
    tldr = extract_tldr(body)
    article_url = absolute_url(args.site_base, slug)
    image_url = absolute_url(args.site_base, slug, image) if image else None

    payload = {
        "subject": title,
        "body": build_email_body(
            title=title,
            description=description,
            tldr=tldr,
            article_url=article_url,
        ),
        "status": "draft",
        "email_type": "public",
        "canonical_url": article_url,
        "description": description,
        "metadata": {
            "source": METADATA_SOURCE,
            METADATA_ARTICLE_KEY: slug,
        },
    }
    if image_url:
        payload["image"] = image_url

    if args.dry_run:
        print(json.dumps(payload, indent=2))
        print(f"\n# dry-run · would {'send' if args.send else 'draft'} for {slug}", file=sys.stderr)
        return 0

    existing = None if args.force else find_existing(
        list_emails(api_base=api_base, api_key=api_key),
        slug,
    )
    if existing:
        print(
            f"Already exists for {slug}: {existing.get('id')} "
            f"({existing.get('status')}) {existing.get('absolute_url')}",
            file=sys.stderr,
        )
        print(existing.get("id") or "")
        return 0

    created = api_request(
        "POST",
        "emails",
        api_base=api_base,
        api_key=api_key,
        payload=payload,
    )
    if not isinstance(created, dict) or not created.get("id"):
        raise SystemExit(f"Unexpected create response: {created}")

    email_id = created["id"]
    print(
        f"Draft created · {email_id} · {created.get('absolute_url')}",
        file=sys.stderr,
    )

    if args.send:
        published = api_request(
            "POST",
            f"emails/{email_id}/publish",
            api_base=api_base,
            api_key=api_key,
            payload={},
        )
        status = published.get("status") if isinstance(published, dict) else "unknown"
        print(f"Publish requested · status={status}", file=sys.stderr)

    print(email_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
