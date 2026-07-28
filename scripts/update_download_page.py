#!/usr/bin/env python3
"""Generate README download links from actual GitHub release assets."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse


BEGIN_MARKER = "<!-- BEGIN CURRENT DOWNLOADS -->"
END_MARKER = "<!-- END CURRENT DOWNLOADS -->"
DEFAULT_REPOSITORY = "framedbyrandy/storytable-testers"
ASSET_PATTERNS = {
    "windows": (
        "Windows",
        "Download StoryTable for Windows",
        re.compile(r"^StoryTable-(\d+\.\d+\.\d+)-Windows-Setup\.exe$"),
    ),
    "macos_apple_silicon": (
        "Mac with an Apple M-series chip",
        "Download StoryTable for Apple Silicon",
        re.compile(
            r"^StoryTable-(\d+\.\d+\.\d+)-macOS-Apple-Silicon\.dmg$"
        ),
    ),
    "macos_intel": (
        "Mac with an Intel processor",
        "Download StoryTable for Intel Mac",
        re.compile(r"^StoryTable-(\d+\.\d+\.\d+)-macOS-Intel\.dmg$"),
    ),
}


def _version_key(version: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in version.split("."))  # type: ignore[return-value]


def select_downloads(releases: list[dict]) -> dict[str, dict]:
    selected: dict[str, dict] = {}
    for release in releases:
        if release.get("draft"):
            continue
        tag = str(release.get("tag_name", ""))
        for asset in release.get("assets", []):
            name = str(asset.get("name", ""))
            url = str(asset.get("browser_download_url", ""))
            for platform, (_, _, pattern) in ASSET_PATTERNS.items():
                match = pattern.fullmatch(name)
                if not match:
                    continue
                version = match.group(1)
                if tag not in {f"v{version}", f"v{version}-beta"}:
                    raise ValueError(
                        f"{name} claims {version}, but its release tag is {tag}"
                    )
                candidate = {
                    "version": version,
                    "name": name,
                    "url": url,
                    "tag": tag,
                }
                current = selected.get(platform)
                if current is None or _version_key(version) > _version_key(
                    current["version"]
                ):
                    selected[platform] = candidate
    missing = sorted(set(ASSET_PATTERNS) - set(selected))
    if missing:
        raise ValueError(
            "No downloadable release asset found for: " + ", ".join(missing)
        )
    return selected


def render_downloads(selected: dict[str, dict]) -> str:
    lines = [BEGIN_MARKER]
    for platform in ASSET_PATTERNS:
        label, link_text, _ = ASSET_PATTERNS[platform]
        item = selected[platform]
        linked_name = unquote(Path(urlparse(item["url"]).path).name)
        if linked_name != item["name"] or item["version"] not in linked_name:
            raise ValueError(
                f"Refusing mismatched label/link for {platform}: "
                f"{item['version']} -> {item['url']}"
            )
        lines.append(
            f"- **{label} - {item['version']}:** "
            f"[{link_text}]({item['url']})"
        )
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_readme(source: str, generated: str) -> str:
    if source.count(BEGIN_MARKER) != 1 or source.count(END_MARKER) != 1:
        raise ValueError("README must contain exactly one generated-download block")
    before, remainder = source.split(BEGIN_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    return before + generated + after


def _request_json(url: str, token: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "storytable-download-page-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers), timeout=30
    ) as response:
        return json.load(response)


def fetch_releases(repository: str, token: str) -> list[dict]:
    releases: list[dict] = []
    for page in range(1, 11):
        batch = _request_json(
            f"https://api.github.com/repos/{repository}/releases"
            f"?per_page=100&page={page}",
            token,
        )
        if not isinstance(batch, list):
            raise ValueError("GitHub releases API returned an unexpected response")
        releases.extend(batch)
        if len(batch) < 100:
            return releases
    raise ValueError("Release scan exceeded 1,000 entries")


def verify_downloads(selected: dict[str, dict], token: str) -> None:
    headers = {"User-Agent": "storytable-download-page-updater"}
    # Release assets in this public tester repository do not require auth.
    # Do not forward a GitHub bearer token to the redirected asset host.
    for item in selected.values():
        request = urllib.request.Request(
            item["url"], headers=headers, method="HEAD"
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise ValueError(
                    f"Download did not resolve successfully: {item['url']}"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY),
    )
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--releases-json", type=Path)
    parser.add_argument("--skip-url-check", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if args.releases_json:
        releases = json.loads(args.releases_json.read_text(encoding="utf-8"))
    else:
        releases = fetch_releases(args.repository, token)
    selected = select_downloads(releases)
    if not args.skip_url_check:
        verify_downloads(selected, token)

    source = args.readme.read_text(encoding="utf-8")
    updated = update_readme(source, render_downloads(selected))
    if args.check:
        if source != updated:
            print("README download block is stale", file=sys.stderr)
            return 1
        return 0
    if source != updated:
        args.readme.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
