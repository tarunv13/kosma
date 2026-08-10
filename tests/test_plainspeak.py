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


def test_supporting_evidence_reads_as_support() -> None:
    reading = plainspeak.house_reading(
        1, "self", "supported", "indicative", [_ev("ashtakavarga", 1)]
    )
    joined = " ".join(reading.body)
    assert "generously supplied" in joined
    assert "nothing in the chart argues the other way" in joined


def test_opposing_evidence_reads_as_strain() -> None:
    reading = plainspeak.house_reading(
        1, "self", "under strain", "indicative", [_ev("ashtakavarga", -1)]
    )
    joined = " ".join(reading.body)
    assert "thinly supplied" in joined
    assert "harder ground" in joined


def test_both_directions_are_woven_into_one_passage() -> None:
    """The reading must connect the two halves, not print two labelled lists.

    Printing "In its favour: ..." above "Against it: ..." is a filing system:
    accurate, and leaving the reader to work out the relation between the two
    themselves.
    """
    reading = plainspeak.house_reading(
        1, "self", "contested", "corroborated", [_ev("aspect", 1), _ev("dignity", -1)]
    )
    joined = " ".join(reading.body)
    assert "At the same time" in joined, "the two directions were not joined"
    for label in ("In its favour:", "Against it:"):
        assert label not in joined, f"reverted to a labelled list: {label!r}"


def test_the_reading_opens_by_saying_what_the_area_is() -> None:
    """Orientation before verdict: a reader is grounded before being read."""
    reading = plainspeak.house_reading(
        7, "partnership", "supported", "indicative", [_ev("aspect", 1)]
    )
    assert "7th house covers" in reading.headline


# Written as code points so the linter does not read the test for dashes as
# itself containing a stray dash.
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def test_no_em_dashes_reach_the_reader() -> None:
    """The house style bans them; generated prose has to obey it too."""
    reading = plainspeak.house_reading(
        2, "wealth", "contested", "well corroborated", [_ev("aspect", 1), _ev("dignity", -1)]
    )
    surfaces = [reading.headline, reading.limit, reading.karaka_note, *reading.body]
    surfaces += list(plainspeak.GLOSSARY.values())
    for text in surfaces:
        assert EM_DASH not in text, f"em dash in: {text[:60]}"
        assert EN_DASH not in text, f"en dash in: {text[:60]}"


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


def test_cited_texts_are_carried_but_kept_out_of_the_passage() -> None:
    """Sources reach the reader after the reading, never inside it.

    Mid-passage, a chapter reference competes with the sentence it supports.
    It is still shown in full; it is shown afterwards.
    """
    reading = plainspeak.house_reading(
        1,
        "self",
        "supported",
        "indicative",
        [_ev("aspect", 1, source="Phaladeepika ch. 6"), _ev("dignity", 1, source="Saravali ch. 3")],
    )
    assert set(reading.sources) == {"Phaladeepika", "Saravali"}
    joined = " ".join(reading.body)
    for text in ("Phaladeepika", "Saravali", "Brihat Parashara"):
        assert text not in joined, f"{text} leaked into the reading passage"


def test_disputed_sources_are_not_credited() -> None:
    """A text cited only by excluded evidence must not appear as a source."""
    reading = plainspeak.house_reading(
        1,
        "self",
        "supported",
        "indicative",
        [
            _ev("aspect", 1, source="Phaladeepika ch. 6"),
            _ev("yoga", 1, disputed=True, source="Saravali ch. 3"),
        ],
    )
    assert "Saravali" not in reading.sources


# ── the whole payload, not just the plain layer ───────────────────────


def test_no_em_dash_anywhere_in_the_rendered_payload() -> None:
    """Every string the client can render has to obey the house style.

    Checking the payload rather than the source is the point: docstrings and
    comments keep their punctuation, and only the text a reader actually sees
    is constrained. This catches a stray dash in any module that contributes
    prose, including ones added later.
    """
    from kosma import api_contract as ac

    payload = ac.build_chart_payload(
        name="Probe",
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

    offenders: list[str] = []

    def walk(node: object, path: str = "") -> None:
        if isinstance(node, str):
            if EM_DASH in node or EN_DASH in node:
                offenders.append(f"{path}: {node[:80]}")
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(payload)
    assert offenders == [], "dashes reached the reader:\n" + "\n".join(offenders)
