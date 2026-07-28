import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "update_download_page.py"
SPEC = importlib.util.spec_from_file_location("update_download_page", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _release(version: str, names: list[str], *, draft: bool = False) -> dict:
    return {
        "tag_name": f"v{version}-beta",
        "draft": draft,
        "assets": [
            {
                "name": name,
                "browser_download_url": (
                    "https://github.com/framedbyrandy/storytable-testers/"
                    f"releases/download/v{version}-beta/{name}"
                ),
            }
            for name in names
        ],
    }


def test_selects_highest_real_asset_per_platform() -> None:
    releases = [
        _release(
            "0.1.98",
            [
                "StoryTable-0.1.98-macOS-Apple-Silicon.dmg",
                "StoryTable-0.1.98-macOS-Intel.dmg",
            ],
        ),
        _release(
            "0.1.72", ["StoryTable-0.1.72-Windows-Setup.exe"]
        ),
        _release(
            "0.1.51",
            [
                "StoryTable-0.1.51-macOS-Apple-Silicon.dmg",
                "StoryTable-0.1.51-macOS-Intel.dmg",
            ],
        ),
    ]

    selected = MODULE.select_downloads(releases)

    assert selected["windows"]["version"] == "0.1.72"
    assert selected["macos_apple_silicon"]["version"] == "0.1.98"
    assert selected["macos_intel"]["version"] == "0.1.98"
    rendered = MODULE.render_downloads(selected)
    assert "Apple M-series chip - 0.1.98" in rendered
    assert "/v0.1.98-beta/StoryTable-0.1.98-macOS-Apple-Silicon.dmg" in rendered


def test_rejects_asset_version_that_disagrees_with_tag() -> None:
    release = _release(
        "0.1.98", ["StoryTable-0.1.54-macOS-Apple-Silicon.dmg"]
    )

    with pytest.raises(ValueError, match="claims 0.1.54"):
        MODULE.select_downloads([release])


def test_draft_release_does_not_advance_downloads() -> None:
    public = _release(
        "0.1.51",
        [
            "StoryTable-0.1.51-Windows-Setup.exe",
            "StoryTable-0.1.51-macOS-Apple-Silicon.dmg",
            "StoryTable-0.1.51-macOS-Intel.dmg",
        ],
    )
    draft = _release(
        "0.1.99",
        [
            "StoryTable-0.1.99-Windows-Setup.exe",
            "StoryTable-0.1.99-macOS-Apple-Silicon.dmg",
            "StoryTable-0.1.99-macOS-Intel.dmg",
        ],
        draft=True,
    )

    selected = MODULE.select_downloads([draft, public])

    assert {item["version"] for item in selected.values()} == {"0.1.51"}
