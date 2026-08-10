"""The plain-language layer must stay honest.

Prose generated from structured evidence is the easiest place in this project
for a claim to appear that the chart does not support. Every test here pins a
property that keeps the sentence and the ledger saying the same thing.
"""

from __future__ import annotations

import pytest

from kosma import plainspeak


def _ev(kind: str, polarity: int, *, disputed: bool = False, source: str = "BPHS ch. 1") -> dict:
    return {
        "id": f"H1-{kind}",
        "house": 1,
        "kind": kind,
        "statement": f"{kind} statement",
        "basis": "basis",
        "source": source,
        "polarity": polarity,
        "disputed": disputed,
    }


# ── the prose must count exactly what the gate counts ─────────────────


def test_disputed_evidence_is_not_narrated() -> None:
    """A disputed factor casts no vote, so it must not appear in the reading."""
    reading = plainspeak.house_reading(
        1,
        "self",
        "supported",
        "indicative",
        [_ev("aspect", 1), _ev("yoga", 1, disputed=True)],
    )
    joined = " ".join(reading.body)
    assert "named combination" not in joined, "a disputed yoga was narrated as if it counted"


def test_disputed_evidence_is_still_disclosed() -> None:
    """Excluded is not the same as hidden: the reader is told it existed."""
    reading = plainspeak.house_reading(
        1, "self", "supported", "indicative", [_ev("aspect", 1), _ev("yoga", 1, disputed=True)]
    )
    assert "disputed" in reading.limit
    assert "1 further factor" in reading.limit


def test_plural_agreement_on_disputed_count() -> None:
    reading = plainspeak.house_reading(
        1,
        "self",
        "supported",
        "indicative",
        [_ev("aspect", 1), _ev("yoga", 1, disputed=True), _ev("dasha", 1, disputed=True)],
    )
    assert "2 further factors" in reading.limit
    assert "are disputed" in reading.limit


# ── direction must not be inverted ────────────────────────────────────


@pytest.mark.parametrize("kind", sorted(plainspeak._KIND_PLAIN))
def test_every_kind_reads_differently_for_and_against(kind: str) -> None:
    """A factor's supporting and opposing phrasing must not be the same text."""
    positive, negative = plainspeak._KIND_PLAIN[kind]
    assert positive != negative
    assert positive and negative


def test_supporting_evidence_lands_in_favour() -> None:
    reading = plainspeak.house_reading(1, "self", "supported", "indicative", [_ev("ashtakavarga", 1)])
    assert any(b.startswith("In its favour") for b in reading.body)
    assert not any(b.startswith("Against it") for b in reading.body)


def test_opposing_evidence_lands_against() -> None:
    reading = plainspeak.house_reading(
        1, "self", "under strain", "indicative", [_ev("ashtakavarga", -1)]
    )
    assert any(b.startswith("Against it") for b in reading.body)
    assert not any(b.startswith("In its favour") for b in reading.body)


def test_generously_and_thinly_supplied_are_not_swapped() -> None:
    good = plainspeak.house_reading(1, "s", "supported", "indicative", [_ev("ashtakavarga", 1)])
    bad = plainspeak.house_reading(1, "s", "under strain", "indicative", [_ev("ashtakavarga", -1)])
    assert "generously supplied" in " ".join(good.body)
    assert "thinly supplied" in " ".join(bad.body)


# ── a withheld house stays withheld ───────────────────────────────────


def test_withheld_reading_claims_nothing() -> None:
    """The plain voice must not become a back door around the gate."""
    w = plainspeak.withheld_reading(8, "crisis and inheritance", "no direction reached threshold")
    text = " ".join([w["headline"], *w["body"]]).lower()
    for leak in ("in its favour", "against it", "well supported", "favourable"):
        assert leak not in text, f"withheld house narrated a direction: {leak!r}"
    assert "finding rather than a gap" in w["headline"]


# ── surface details ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("n", "expected"),
    [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (11, "11th"), (12, "12th")],
)
def test_ordinals(n: int, expected: str) -> None:
    assert plainspeak._ordinal(n) == expected


def test_every_factor_kind_has_a_plain_label() -> None:
    """The technical panel names kinds in English; none may fall through."""
    assert set(plainspeak.KIND_LABEL) == set(plainspeak._KIND_PLAIN)


def test_glossary_entries_are_sentences_not_stubs() -> None:
    for term, meaning in plainspeak.GLOSSARY.items():
        assert len(meaning) > 25, f"{term} has a stub definition"
        assert meaning[0].isupper(), f"{term} definition does not start as a sentence"


def test_cited_texts_are_named_in_the_prose() -> None:
    """A reader is told which book a rule came from, not just that one exists."""
    reading = plainspeak.house_reading(
        1,
        "self",
        "supported",
        "indicative",
        [_ev("aspect", 1, source="Phaladeepika ch. 6"), _ev("dignity", 1, source="Saravali ch. 3")],
    )
    joined = " ".join(reading.body)
    assert "Phaladeepika" in joined
    assert "Saravali" in joined
