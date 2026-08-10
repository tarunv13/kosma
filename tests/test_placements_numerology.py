"""Placements and numerology: complete, per-chart, and honestly bounded."""

from __future__ import annotations

from datetime import date

import pytest

from kosma import numerology as num
from kosma import placements as pl
from kosma.api_contract import GLYPHS, SYMBOLS
from kosma.interpretations import HOUSE_GOVERNS
from kosma.vedic_engine import VEDIC_PLANETS

HOUSES = range(1, 13)


# ── every combination must exist and be distinct ──────────────────────


@pytest.mark.parametrize("planet", VEDIC_PLANETS)
@pytest.mark.parametrize("house", HOUSES)
def test_every_planet_in_every_house_reads(planet: str, house: int) -> None:
    r = pl.placement_reading(planet, house, "Aries", "neutral")
    assert r.signifies and r.strengths and r.weaknesses and r.nature
    assert r.remedy["mantra"]
    # the house's own subject must actually appear in the text
    assert str(house) in r.signifies or HOUSE_GOVERNS[house].split(",")[0].lower()[:12] in (
        r.signifies.lower()
    )


def test_all_nine_grahas_are_covered() -> None:
    assert set(pl.GRAHAS) == set(VEDIC_PLANETS)
    assert set(GLYPHS) == set(VEDIC_PLANETS)
    assert set(SYMBOLS) == set(VEDIC_PLANETS)


def test_symbols_are_distinct_and_non_empty() -> None:
    """A duplicated or blank symbol makes two planets indistinguishable."""
    assert len(set(SYMBOLS.values())) == len(SYMBOLS)
    for planet, sym in SYMBOLS.items():
        assert sym.strip(), f"{planet} has a blank symbol"


def test_abbreviations_stay_alongside_symbols() -> None:
    """The two-letter form is the fallback when a font lacks the glyph."""
    for planet in VEDIC_PLANETS:
        assert len(GLYPHS[planet]) == 2
        assert GLYPHS[planet].isascii(), "the fallback must not itself need a font"


# ── the reading must be about THIS chart, not the abstract combination ─


def test_dignity_changes_the_reading() -> None:
    strong = pl.placement_reading("Saturn", 7, "Libra", "exalted")
    weak = pl.placement_reading("Saturn", 7, "Aries", "debilitated")
    assert strong.condition != weak.condition
    assert "milder risk" in strong.condition
    assert "worked for" in weak.condition


def test_retrograde_and_combustion_are_stated() -> None:
    r = pl.placement_reading("Mercury", 3, "Gemini", "own sign", retrograde=True, combust=True)
    assert "retrograde" in r.condition
    assert "combust" in r.condition


def test_benefic_in_dusthana_is_flagged() -> None:
    r = pl.placement_reading("Jupiter", 6, "Virgo", "enemy")
    assert "partly consumed" in r.condition


# Exactly the strings kosma.dignity emits. Written out rather than derived so
# that a change to the engine's wording fails here loudly instead of silently
# producing "Sun is neutral sign" in the interface, which is what happened.
ENGINE_DIGNITIES = (
    "exalted",
    "debilitated",
    "moolatrikona",
    "own sign",
    "great friend's sign",
    "friend's sign",
    "neutral sign",
    "enemy's sign",
    "great enemy's sign",
)


@pytest.mark.parametrize(
    ("dignity", "expected"),
    [
        ("own sign", "is in its own sign"),
        ("moolatrikona", "is in its moolatrikona"),
        ("exalted", "is exalted"),
        ("debilitated", "is debilitated"),
        ("neutral sign", "sits in a neutral sign"),
        ("enemy's sign", "sits in an enemy's sign"),
        ("great enemy's sign", "sits in a great enemy's sign"),
        ("friend's sign", "sits in a friend's sign"),
        ("great friend's sign", "sits in a great friend's sign"),
    ],
)
def test_dignity_reads_as_english(dignity: str, expected: str) -> None:
    """The engine's states are noun phrases; prose needs the preposition."""
    assert expected in pl._dignity_phrase("Saturn", dignity)


@pytest.mark.parametrize("dignity", ENGINE_DIGNITIES)
def test_every_engine_dignity_forms_a_sentence(dignity: str) -> None:
    """No state may produce "Sun is neutral sign" or similar."""
    phrase = pl._dignity_phrase("Sun", dignity)
    assert phrase.startswith("Sun is ") or phrase.startswith("Sun sits in ")
    # "is <noun phrase>" without an article is the failure mode being pinned.
    assert not phrase.endswith("is neutral sign")
    assert " is enemy" not in phrase


@pytest.mark.parametrize(
    ("dignity", "expect_strong"),
    [
        ("exalted", True),
        ("own sign", True),
        ("moolatrikona", True),
        ("friend's sign", True),
        ("great friend's sign", True),
        ("debilitated", False),
        ("enemy's sign", False),
        ("great enemy's sign", False),
    ],
)
def test_dignity_classification_is_not_inverted(dignity: str, expect_strong: bool) -> None:
    """A friend's sign must not be read as an enemy's, or the advice inverts."""
    r = pl.placement_reading("Sun", 5, "Leo", dignity)
    if expect_strong:
        assert "milder risk" in r.condition
    else:
        assert "worked for" in r.condition


def test_real_engine_dignities_round_trip_through_a_reading() -> None:
    """Every state the engine can emit must produce usable prose."""
    for dignity in ENGINE_DIGNITIES:
        r = pl.placement_reading("Venus", 7, "Libra", dignity)
        assert "In this chart Venus" in r.condition


def test_house_classes_are_correct() -> None:
    assert "kendra" in pl.house_classes(10)
    assert "trikona" in pl.house_classes(9)
    assert "dusthana" in pl.house_classes(8)
    assert "upachaya" in pl.house_classes(11)
    # the 1st is both angular and a trine
    assert set(pl.house_classes(1)) == {"kendra", "trikona"}
    # the 6th and 10th are each in two groups
    assert set(pl.house_classes(6)) == {"dusthana", "upachaya"}


def test_remedies_are_per_graha_never_per_combination() -> None:
    """The same planet must offer the same upaya wherever it falls."""
    a = pl.placement_reading("Mars", 1, "Aries", "own sign").remedy
    b = pl.placement_reading("Mars", 12, "Pisces", "neutral").remedy
    assert a == b, "a remedy was invented for a specific placement"


# ── numerology stays outside the gate ─────────────────────────────────


def test_numbers_map_to_grahas_within_range() -> None:
    assert set(num.NUMBER_GRAHA) == set(range(1, 10))
    assert set(num.NUMBER_MEANING) == set(range(1, 10))


def test_mulank_is_the_day_reduced() -> None:
    r = num.compute("Anyone", date(1993, 2, 13))
    assert r["mulank"]["number"] == 4  # 1 + 3


def test_master_numbers_survive_reduction() -> None:
    assert num._reduce(29) == 11
    assert num._reduce(38) == 11
    assert num._reduce(29, keep_master=False) == 2


def test_the_two_name_systems_are_both_reported_when_they_differ() -> None:
    """Picking a winner would hide a real disagreement between traditions."""
    r = num.compute("Tarun Kumar Verma", date(1993, 2, 13))
    assert r["name_chaldean"] is not None
    assert r["name_pythagorean"] is not None
    if not r["systems_agree"]:
        assert "disagree" in r["disagreement"]


def test_missing_name_does_not_fabricate_a_number() -> None:
    r = num.compute("", date(2000, 1, 1))
    assert r["name_chaldean"] is None
    assert r["name_pythagorean"] is None
    assert r["mulank"] is not None, "date-derived numbers still work without a name"


def test_numerology_states_that_it_casts_no_vote() -> None:
    r = num.compute("Anyone", date(2000, 1, 1))
    assert "no vote" in r["note"]


# ── the symbol font must be trusted only per glyph ────────────────────


def test_symbol_coverage_is_checked_per_glyph() -> None:
    """A font with partial coverage must not license every symbol.

    Most faces carrying the planets are missing the lunar nodes, U+260A and
    U+260B. Deciding coverage from the set as a whole -- the first attempt
    here compared string widths -- accepts such a font and then draws a box
    for Rahu and Ketu.
    """
    from kosma import pdf_generator as pg

    for planet in pg.SYMBOLS:
        sigil = pg._sigil(planet)
        if planet in pg.SYMBOL_OK:
            assert pg.SYMBOLS[planet] in sigil
        else:
            assert sigil == pg.ABBREV[planet]
            assert pg.SYMBOLS[planet] not in sigil


def test_no_symbol_font_still_renders_every_planet() -> None:
    """With no font at all, every planet must still print something."""
    from kosma import pdf_generator as pg

    saved_font, saved_ok = pg.SYMBOL_FONT, pg.SYMBOL_OK
    try:
        pg.SYMBOL_FONT, pg.SYMBOL_OK = None, frozenset()
        for planet in pg.SYMBOLS:
            assert pg._sigil(planet) == pg.ABBREV[planet]
    finally:
        pg.SYMBOL_FONT, pg.SYMBOL_OK = saved_font, saved_ok
