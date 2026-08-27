"""Deterministic submission-packaging tests (PP-81).

These keep the final deliverables honest: the demo video must exist at a
versioned path, be a real MP4 whose declared resolution meets the challenge
minimum (>=1440x900), the SHA manifest must list every delivered ticket with
valid commit ids, and the SUBMISSION checklist must point at artifacts that
actually exist in the tree.
"""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VIDEO_GLOB = "devnetwork-demo-*.mp4"
DELIVERED_TICKETS = ("PP-63", "PP-79", "PP-80", "PP-81")


def _read(relative: str) -> str:
    return (REPO / relative).read_text(encoding="utf-8")


def _demo_videos() -> list[Path]:
    return sorted((REPO / "evidence" / "demo").glob(VIDEO_GLOB))


def test_sha_manifest_lists_every_delivered_ticket() -> None:
    manifest = _read("docs/SHA_MANIFEST.md")
    for ticket in DELIVERED_TICKETS:
        assert re.search(rf"\b{ticket}\b", manifest), f"SHA manifest missing {ticket}"
    # every lineage row that claims a commit carries a plausible 7-40 hex id
    for row in manifest.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if (
            len(cells) >= 2
            and re.match(r"^(repo init|PP-\d+)", cells[0])
            and "see delivery packet" not in cells[1]
        ):
            assert re.search(r"[0-9a-f]{7,40}", cells[1]), (
                f"manifest lineage row lacks commit id: {row[:60]}"
            )


def test_demo_video_exists_at_versioned_path() -> None:
    videos = _demo_videos()
    assert videos, "no evidence/demo/devnetwork-demo-*.mp4 found"
    for video in videos:
        assert re.search(r"-\d{8}T\d{4}Z\.mp4$", video.name), (
            f"video filename must be versioned (SHA/timestamp), got {video.name}"
        )


def _mp4_track_dimensions(path: Path) -> tuple[int, int]:
    """Parse the first tkhd box of an MP4 for its declared width/height."""
    data = path.read_bytes()
    assert data[4:8] == b"ftyp", f"{path.name} is not an MP4 (no ftyp box)"
    idx = data.find(b"tkhd")
    assert idx != -1, f"{path.name} has no tkhd box"
    payload = data[idx + 4 : idx + 4 + 84]  # full v0 payload through the matrix
    width = struct.unpack(">I", payload[-8:-4])[0] >> 16
    height = struct.unpack(">I", payload[-4:])[0] >> 16
    return width, height


def test_demo_video_meets_minimum_resolution() -> None:
    for video in _demo_videos():
        width, height = _mp4_track_dimensions(video)
        assert width >= 1440 and height >= 900, (
            f"{video.name} is {width}x{height}; challenge minimum is 1440x900"
        )


def test_submission_checklist_matches_artifacts() -> None:
    submission = _read("docs/SUBMISSION.md")
    row10 = next(line for line in submission.splitlines() if line.startswith("| 10|"))
    assert "✅ Delivered" in row10, "checklist row 10 must be delivered"
    videos = _demo_videos()
    assert videos, "row 10 delivered but no demo video in evidence/demo/"
    # the manifest and checklist must reference the same video artifact
    manifest = _read("docs/SHA_MANIFEST.md")
    for video in videos:
        assert video.name in manifest, f"{video.name} not recorded in SHA_MANIFEST.md"
        assert video.name in submission, f"{video.name} not referenced in SUBMISSION.md row 10"


def test_agent_catalog_count_is_consistent() -> None:
    catalog = json.loads((REPO / "data" / "agents.json").read_text(encoding="utf-8"))
    slugs = [agent["slug"] for agent in catalog["agents"]]
    assert len(slugs) >= 10, "fleet catalog shrank below the shipped 10 agents"
    assert len(set(slugs)) == len(slugs), "duplicate agent slugs in catalog"
    demo = (REPO / "scripts" / "demo.sh").read_text(encoding="utf-8")
    assert "count" in demo and "ppaa-builder" in demo, "demo script no longer exercises the catalog"
