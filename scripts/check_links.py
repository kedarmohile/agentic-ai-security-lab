#!/usr/bin/env python3
"""Repository hyperlink checker.

Default mode validates repository-relative Markdown/HTML links and console assets.
Use --external for an explicit live audit of unique http(s) destinations.

External checks are intentionally opt-in so CI is not coupled to third-party uptime.
"""

from __future__ import annotations

import argparse
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CONSOLE_ASSETS = ROOT / "src" / "agentic_ai_security_lab" / "console_assets"

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_LINK_RE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
EXTERNAL_RE = re.compile(r"https?://[^\s<>'\")\]]+")


@dataclass(frozen=True)
class LinkProblem:
    source: Path
    target: str
    reason: str


def markdown_slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text.strip().lower())
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def markdown_anchors(path: Path) -> set[str]:
    if not path.is_file() or path.suffix.lower() != ".md":
        return set()
    anchors: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            anchors.add(markdown_slug(match.group(1)))
    return anchors


def link_targets(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    values: list[str] = []
    seen: set[str] = set()
    patterns = [MARKDOWN_LINK_RE]
    if path.suffix.lower() in {".html", ".htm"}:
        patterns.append(HTML_LINK_RE)
    for pattern in patterns:
        for match in pattern.finditer(content):
            target = match.group(1)
            if target not in seen:
                seen.add(target)
                values.append(target)
    return values


def source_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() in {".md", ".html", ".htm"}:
            yield path


def validate_internal_links() -> list[LinkProblem]:
    problems: list[LinkProblem] = []
    for source in source_files():
        for raw in link_targets(source):
            if raw.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
                continue

            decoded = urllib.parse.unquote(raw)
            path_part, _, fragment = decoded.partition("#")

            if not path_part and fragment:
                if fragment.lower() not in markdown_anchors(source):
                    problems.append(LinkProblem(source, raw, "missing anchor"))
                continue

            if raw.startswith("/"):
                target = CONSOLE_ASSETS / raw.lstrip("/")
            else:
                target = (source.parent / path_part).resolve()

            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                problems.append(LinkProblem(source, raw, "target escapes repository"))
                continue

            if not target.exists():
                problems.append(LinkProblem(source, raw, "missing file"))
                continue

            if fragment and target.suffix.lower() == ".md":
                if fragment.lower() not in markdown_anchors(target):
                    problems.append(LinkProblem(source, raw, "missing target anchor"))

    return problems


def discover_external_urls() -> list[str]:
    urls: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".md", ".html", ".htm", ".py", ".js"}:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for match in EXTERNAL_RE.finditer(content):
            url = match.group(0).rstrip(".,;:")
            parsed = urllib.parse.urlparse(url)
            if parsed.hostname in {"127.0.0.1", "localhost"}:
                continue
            if "{" in url or "}" in url:
                continue
            urls.add(url)
    return sorted(urls)


def check_external_url(url: str, timeout: float = 15.0) -> tuple[bool, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AASL-Link-Audit/1.0 (+https://github.com/kedarmohile/agentic-ai-security-lab)"
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return True, f"HTTP {exc.code} (protected/requires auth)"
        return False, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"URL error: {exc.reason}"
    except TimeoutError:
        return False, "timeout"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--external",
        action="store_true",
        help="Also perform live HTTP checks against unique external destinations.",
    )
    args = parser.parse_args()

    problems = validate_internal_links()
    if problems:
        print("Internal link problems:")
        for problem in problems:
            rel = problem.source.relative_to(ROOT)
            print(f"- {rel}: {problem.target} -> {problem.reason}")
        return 1

    print("Internal repository links: OK")

    urls = discover_external_urls()
    print(f"External destinations discovered: {len(urls)}")

    if not args.external:
        print("External live checks skipped (use --external).")
        return 0

    failed = False
    for url in urls:
        ok, detail = check_external_url(url)
        mark = "OK" if ok else "FAIL"
        print(f"[{mark}] {url} - {detail}")
        failed = failed or not ok

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
