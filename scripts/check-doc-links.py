#!/usr/bin/env python3
"""Check repository-local links and Markdown anchors without network access."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from urllib.parse import unquote, urlsplit


MARKDOWN_LINK = re.compile(
    r"!?\[[^\]\n]*\]\((?P<destination><[^>\n]+>|[^\s)\n]+)"
    r"(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\)"
)
REFERENCE_LINK = re.compile(
    r"^\s{0,3}\[[^\]\n]+\]:\s*(?P<destination><[^>\n]+>|\S+)",
    re.MULTILINE,
)
HTML_LINK = re.compile(
    r"\b(?:href|src)\s*=\s*[\"'](?P<destination>[^\"']+)[\"']",
    re.IGNORECASE,
)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*#*\s*$")
SETEXT = re.compile(r"^\s*(?:=+|-+)\s*$")
HTML_ID = re.compile(r"\b(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
EXPLICIT_ID = re.compile(r"\{:\s*#([^\s}]+)[^}]*\}")
FENCE = re.compile(r"^\s*(```+|~~~+)")
SKIP_PARTS = {".git", "_site", "assets.generated", "docs/doxygen", "build"}


def repository_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "*.md",
            "*.html",
        ],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    files = []
    for name in result.stdout.splitlines():
        path = Path(name)
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if (root / path).is_file():
            files.append(path)
    return sorted(files)


def rendered_files(root: Path) -> list[Path]:
    """List rendered HTML/Markdown files under a built site directory."""
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".md"}
    )


def github_slug(title: str) -> str:
    title = re.sub(r"!?(?:\[([^\]]+)\]\([^)]*\))", r"\1", title)
    title = re.sub(r"<[^>]+>", "", title)
    title = re.sub(r"[`*_~]", "", title)
    title = unicodedata.normalize("NFKC", title).strip().lower()
    title = "".join(
        character
        for character in title
        if character in " -_" or character.isalnum()
    )
    return re.sub(r"[\s-]+", "-", title).strip("-")


def document_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors = {unquote(value) for value in HTML_ID.findall(text)}
    anchors.update(unquote(value) for value in EXPLICIT_ID.findall(text))
    if "{% include generated-snapshot.md %}" in text:
        for parent in path.parents:
            pass_data = parent / "_data" / "generated_passes.yml"
            if pass_data.is_file():
                anchors.update(
                    re.findall(
                        r"^\s*id:\s*([^\s#]+)",
                        pass_data.read_text(encoding="utf-8"),
                        re.MULTILINE,
                    )
                )
                break
    if path.suffix.lower() != ".md":
        return anchors

    counts: defaultdict[str, int] = defaultdict(int)
    lines = text.splitlines()
    fenced = False
    fence_marker = ""
    for index, line in enumerate(lines):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if not fenced:
                fenced = True
                fence_marker = marker
            elif marker == fence_marker:
                fenced = False
            continue
        if fenced:
            continue

        match = HEADING.match(line)
        title = match.group("title") if match else ""
        if not match and index + 1 < len(lines) and SETEXT.match(lines[index + 1]):
            title = line.strip()
        if not title:
            continue
        title = EXPLICIT_ID.sub("", title).strip()
        slug = github_slug(title)
        if not slug:
            continue
        suffix = counts[slug]
        anchors.add(slug if suffix == 0 else f"{slug}-{suffix}")
        counts[slug] += 1
    return anchors


def destination_values(text: str) -> list[tuple[int, str]]:
    visible_lines: list[str] = []
    fenced = False
    fence_marker = ""
    for line in text.splitlines(keepends=True):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[0]
            if not fenced:
                fenced = True
                fence_marker = marker
            elif marker == fence_marker:
                fenced = False
            visible_lines.append("\n" if line.endswith("\n") else "")
            continue
        visible_lines.append(("\n" if line.endswith("\n") else "") if fenced else line)
    text = "".join(visible_lines)
    values: list[tuple[int, str]] = []
    for pattern in (MARKDOWN_LINK, REFERENCE_LINK, HTML_LINK):
        for match in pattern.finditer(text):
            destination = match.group("destination")
            if destination.startswith("<") and destination.endswith(">"):
                destination = destination[1:-1]
            line = text.count("\n", 0, match.start()) + 1
            values.append((line, destination))
    return values


def local_target(root: Path, source: Path, destination: str) -> tuple[Path | None, str]:
    if not destination or destination.startswith("#"):
        return source, unquote(destination.removeprefix("#"))
    if "{{" in destination or "{%" in destination:
        return None, ""

    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or destination.startswith("//"):
        return None, ""

    path_text = unquote(parsed.path)
    if path_text.startswith("/cartofreako/"):
        path_text = path_text.removeprefix("/cartofreako/")
    elif path_text.startswith("/"):
        path_text = path_text.removeprefix("/")
    base = root if parsed.path.startswith("/") else (root / source).parent
    target = (base / path_text).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return target, unquote(parsed.fragment)
    return target, unquote(parsed.fragment)


def rendered_source(target: Path) -> Path | None:
    if target.is_dir():
        for name in ("README.md", "index.md", "index.html"):
            candidate = target / name
            if candidate.is_file():
                return candidate
        return target
    if target.is_file():
        return target
    if target.suffix.lower() == ".html":
        markdown = target.with_suffix(".md")
        if markdown.is_file():
            return markdown
    if not target.suffix:
        markdown = target.with_suffix(".md")
        if markdown.is_file():
            return markdown
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--walk",
        type=Path,
        help="validate a rendered site directory (for example _site) instead of git-tracked sources",
    )
    args = parser.parse_args()
    walk_mode = args.walk is not None
    root = args.walk.resolve() if walk_mode else args.root.resolve()
    files = rendered_files(root) if walk_mode else repository_files(root)
    anchor_cache: dict[Path, set[str]] = {}
    errors: list[str] = []
    checked = 0

    for source in files:
        text = (root / source).read_text(encoding="utf-8")
        for line, destination in destination_values(text):
            target, fragment = local_target(root, source, destination)
            if target is None:
                continue
            checked += 1
            resolved = rendered_source(target)
            if resolved is None:
                errors.append(f"{source}:{line}: missing local target: {destination}")
                continue
            if (
                fragment
                and not walk_mode
                and resolved.suffix.lower() in {".md", ".html"}
            ):
                anchors = anchor_cache.setdefault(resolved, document_anchors(resolved))
                if fragment not in anchors:
                    errors.append(
                        f"{source}:{line}: missing anchor #{fragment} in "
                        f"{resolved.relative_to(root)}"
                    )

    if errors:
        print(f"documentation link check failed: {len(errors)} error(s)", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"documentation link check passed: {len(files)} files, {checked} local links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
