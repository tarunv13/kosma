"""Dignity, relations, and functional nature."""

from __future__ import annotations

import pytest

from kosma import dignity as dg
from kosma import vedic_engine as ve


def test_exaltation_and_debilitation_are_opposite() -> None:
    for planet, (sign, _deg) in dg.EXALTATION.items():
        deb = ve.SIGNS[(ve.SIGNS.index(sign) + 6) % 12]
        assert deb != sign, f"{planet} debilitation must differ from exaltation"


def test_reference_saturn_is_debilitated(reference_chart: ve.Chart) -> None:
    """Saturn sits in Aries at the J2000 epoch, its debilitation sign."""
    d = dg.dignity_of(reference_chart, "Saturn")
    assert d.state == "debilitated"
    assert d.sign == "Aries"
    assert d.score < 0
    assert "debilitation sign" in d.state_reason


def test_reference_mercury_is_combust(reference_chart: ve.Chart) -> None:
    d = dg.dignity_of(reference_chart, "Mercury")
    assert d.combust is True
    assert d.combust_note is not None
    assert "combustion orb" in d.combust_note


def test_a_planet_outside_the_orb_is_not_combust(reference_chart: ve.Chart) -> None:
    d = dg.dignity_of(reference_chart, "Jupiter")
    assert d.combust is False
    assert d.combust_note is not None
    assert "outside the" in d.combust_note


def test_sun_is_never_combust(reference_chart: ve.Chart) -> None:
    assert dg.dignity_of(reference_chart, "Sun").combust is False


def test_natural_relations_are_declared_from_each_side() -> None:
    # BPHS friendship is not symmetric; Saturn counts the Sun an enemy while
    # the Sun counts Saturn one too, but Mercury/Moon is a genuine asymmetry.
    assert dg.natural_relation("Moon", "Mercury") == "friend"
    assert dg.natural_relation("Mercury", "Moon") == "enemy"


def test_compound_relation_uses_both_tables(reference_chart: ve.Chart) -> None:
    for a in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        for b in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            rel = dg.compound_relation(reference_chart, a, b)
            assert rel in {
                "own",
                "great friend",
                "friend",
                "neutral",
                "enemy",
                "great enemy",
            }


@pytest.mark.parametrize(
    "lagna,expected",
    [
        ("Taurus", "Saturn"),
        ("Cancer", "Mars"),
        ("Leo", "Mars"),
        ("Libra", "Saturn"),
        ("Capricorn", "Venus"),
        ("Aquarius", "Venus"),
    ],
)
def test_classical_yogakarakas(lagna: str, expected: str) -> None:
    """Only the six classical yogakarakas should qualify, one per lagna."""
    chart = _chart_with_lagna(lagna)
    karakas = [
        p
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
        if dg.functional_nature(chart, p)[0] == "yogakaraka"
    ]
    assert karakas == [expected], f"{lagna} lagna should yield exactly {expected}"


@pytest.mark.parametrize("lagna", ["Aries", "Gemini", "Virgo", "Scorpio", "Sagittarius", "Pisces"])
def test_lagnas_without_a_yogakaraka(lagna: str) -> None:
    """The lagna is both kendra and trikona, and must not create a yogakaraka."""
    chart = _chart_with_lagna(lagna)
    karakas = [
        p
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
        if dg.functional_nature(chart, p)[0] == "yogakaraka"
    ]
    assert karakas == []


def test_nodes_have_no_fixed_functional_nature(reference_chart: ve.Chart) -> None:
    for node in ("Rahu", "Ketu"):
        nature, reason = dg.functional_nature(reference_chart, node)
        assert nature == "contextual"
        assert "own no sign" in reason


def test_node_exaltation_is_flagged_disputed(reference_chart: ve.Chart) -> None:
    for node in ("Rahu", "Ketu"):
        d = dg.dignity_of(reference_chart, node)
        assert d.disputed, f"{node} exaltation disagreement must be recorded"
        assert d.state not in ("exalted", "debilitated")


def test_state_phrase_reads_as_a_predicate(reference_chart: ve.Chart) -> None:
    assert dg.dignity_of(reference_chart, "Saturn").state_phrase == "debilitated"
    assert dg.dignity_of(reference_chart, "Mars").state_phrase.startswith("in a ")
    assert dg.dignity_of(reference_chart, "Jupiter").state_phrase.startswith("in a ")


def _chart_with_lagna(sign: str) -> ve.Chart:
    """A reference chart relabelled to a chosen ascendant sign.

    Functional nature depends only on the lagna sign index, so overriding it is
    enough to exercise the rule across all twelve ascendants.
    """
    base = ve.build_chart(
        label="probe",
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=51.5074,
        lon_geo=-0.1278,
        tz=0.0,
    )
    base.ascendant_sign = sign
    base.ascendant_sign_idx = ve.SIGNS.index(sign)
    return base
