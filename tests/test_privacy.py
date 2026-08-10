"""Privacy guarantees, asserted rather than promised.

This project's headline claim is that birth data is sensitive. Every item here
was a real leak at some point in the repository's history, so each one is
pinned: a future refactor that reintroduces it fails the build instead of
quietly shipping.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kosma import pdf_generator
from kosma.main import _anonymous_rate_key, app

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


class _FakeRequest:
    def __init__(self, ip: str) -> None:
        self.client = type("C", (), {"host": ip})()
        self.headers: dict[str, str] = {}
        self.scope = {"client": (ip, 0)}


# ── the rate limiter must not retain addresses ────────────────────────


def test_rate_limit_key_is_not_the_ip() -> None:
    ip = "203.0.113.42"
    key = _anonymous_rate_key(_FakeRequest(ip))
    assert ip not in key
    assert len(key) == 32, "expected a blake2b digest, not a passthrough"


def test_rate_limit_key_is_stable_and_distinguishing() -> None:
    """It has to still work as a bucket: same caller same key, others differ."""
    a1 = _anonymous_rate_key(_FakeRequest("203.0.113.42"))
    a2 = _anonymous_rate_key(_FakeRequest("203.0.113.42"))
    b = _anonymous_rate_key(_FakeRequest("198.51.100.7"))
    assert a1 == a2
    assert a1 != b


# ── the PDF must not carry hidden metadata about the reader ───────────


def _pdf_for(name: str) -> str:
    return pdf_generator.generate_pdf(
        name=name,
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=51.5074,
        lon=-0.1278,
        tz=0.0,
        place="London, UK",
    ).decode("latin-1")


def test_pdf_timestamps_are_invariant() -> None:
    """A /CreationDate records to the second when someone sought a reading."""
    raw = _pdf_for("Probe Person")
    for field in ("/CreationDate", "/ModDate"):
        match = re.search(rf"{field}\s*\((.*?)\)", raw)
        assert match, f"{field} missing entirely, which is also fine"
        assert not match.group(1).startswith("D:20") or match.group(1).startswith("D:20000101"), (
            f"{field} still carries a real timestamp"
        )


def test_pdf_info_dictionary_holds_no_name() -> None:
    raw = _pdf_for("Probe Person")
    info = re.search(r"/Info.*?>>", raw, re.S)
    if info:
        assert "Probe Person" not in info.group(0)


def test_two_pdfs_of_the_same_chart_are_identical() -> None:
    """Byte-identical output proves no clock or nonce leaked into the file."""
    from datetime import UTC, datetime

    pinned = datetime(2026, 5, 25, tzinfo=UTC)
    args = {
        "name": "Probe",
        "year": 2000,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 51.5074,
        "lon": -0.1278,
        "tz": 0.0,
        "place": "London, UK",
        "today": pinned,
    }
    assert pdf_generator.generate_pdf(**args) == pdf_generator.generate_pdf(**args)


# ── headers ───────────────────────────────────────────────────────────


def test_response_headers_do_not_advertise_the_stack(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.headers.get("server") == "kosma"
    assert "uvicorn" not in r.headers.get("server", "").lower()


def test_responses_are_marked_unindexable(client: TestClient) -> None:
    r = client.get("/")
    assert "noindex" in r.headers.get("x-robots-tag", "")
    assert r.headers.get("cross-origin-resource-policy") == "same-origin"


# ── the repository itself must stay free of personal readings ─────────

FORBIDDEN_PATTERNS = (
    "shilpa",
    "surbhi",
    "sunariwal",
    "balotra",
    "25.8333",
    "72.2333",
)

SCANNED_SUFFIXES = {".py", ".md", ".ts", ".tsx", ".html", ".css", ".yml", ".toml"}
SKIP_DIRS = {".git", ".venv", "node_modules", ".next", ".mypy_cache", ".ruff_cache", ".claude"}


# Two files legitimately contain these strings.
#
# `cities.py` is a public geography table. A town's name and coordinates are
# not personal data — what made the old reference chart personal was the
# *combination* of a name, a date and a time with a place. Removing Balotra
# from a list of 149 cities would protect nobody and would break the lookup
# for anyone born there.
#
# This file holds the patterns because it is the thing doing the searching.
EXEMPT = {"cities.py", "test_privacy.py"}


def _tracked_text_files() -> list[Path]:
    out = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.suffix not in SCANNED_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in EXEMPT:
            continue
        out.append(p)
    return out


def test_no_personal_reading_is_committed() -> None:
    """The docs directory must never hold a named person's chart again."""
    strays = [
        p.name
        for p in (REPO / "docs").glob("*")
        if any(t in p.name.lower() for t in ("soul-blueprint", "week-ahead"))
        and p.name != "sample-blueprint.pdf"
    ]
    assert strays == [], f"personal readings found in docs/: {strays}"


def test_no_real_birth_data_in_tracked_source() -> None:
    """The reference chart is a synthetic epoch; nobody's birth should appear."""
    offenders: list[str] = []
    for path in _tracked_text_files():
        lowered = path.read_text(encoding="utf-8", errors="ignore").lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in lowered:
                offenders.append(f"{path.relative_to(REPO)} :: {pattern}")
    assert offenders == [], "real birth data reintroduced:\n" + "\n".join(offenders)


# ── the report must not print boxes where symbols were meant ──────────
#
# ReportLab's Helvetica is Type 1/WinAnsi and has no glyph for U+2609..U+264F,
# U+211E or U+26A0. Requesting one does not raise -- it draws notdef, a filled
# black square. Three separate markers in this report did exactly that: the
# planet symbols, the wheel's retrograde mark, and the tag on disputed
# evidence, which is the single most important thing on the page to label
# legibly.


def test_report_contains_no_notdef_boxes() -> None:
    """Any glyph the font lacks renders as a box; none may reach the reader."""
    from pypdf import PdfReader

    raw = pdf_generator.generate_pdf(
        name="Probe Person",
        year=1993,
        month=2,
        day=13,
        hour=9,
        minute=30,
        lat=51.5074,
        lon=-0.1278,
        tz=0.0,
        place="London, UK",
    )
    import io

    text = "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    assert "■" not in text, (
        "the report drew a notdef box: a symbol was requested from a font that has no glyph for it"
    )


def test_planet_symbols_fall_back_rather_than_break() -> None:
    """With no symbol font, abbreviations are used -- never an empty string."""
    for planet in pdf_generator.SYMBOLS:
        assert pdf_generator.ABBREV[planet].isascii()
        assert len(pdf_generator.ABBREV[planet]) == 2
    # _sigil must always yield something renderable either way.
    for planet in pdf_generator.SYMBOLS:
        assert pdf_generator._sigil(planet).strip()
