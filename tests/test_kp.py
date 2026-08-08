"""KP star/sub/sub-sub lord tests."""

from __future__ import annotations

import pytest

from kosma import vedic_engine as ve


def test_kp_star_lord_at_zero_aries() -> None:
    """0 deg Aries is in Ashwini, ruled by Ketu."""
    star, _sub, _ss = ve.kp_sublord(0.0)
    assert star == "Ketu"


def test_kp_star_lord_for_each_nakshatra_start() -> None:
    """At the start of every nakshatra, the star lord must match the table."""
    span = 360.0 / 27
    for i, expected in enumerate(ve.NAKSHATRA_LORDS):
        # Inside the nakshatra, just a hair past the boundary.
        lon = i * span + 0.001
        star, _, _ = ve.kp_sublord(lon)
        assert star == expected, f"nakshatra {ve.NAKSHATRAS[i]} expected {expected}, got {star}"


def test_kp_sub_starts_with_star_lord() -> None:
    """The first sub of every nakshatra is its own star lord (Vimshottari order)."""
    span = 360.0 / 27
    for i in range(27):
        lon = i * span + 0.0001
        star, sub, _ = ve.kp_sublord(lon)
        assert sub == star


def test_kp_chain_for_reference_ascendant(reference_chart: ve.Chart) -> None:
    """J2000 asc is Aries 0 09' 40.9" — KP chain Ketu / Ketu / Venus."""
    star, sub, ss = ve.kp_sublord(reference_chart.ascendant_lon)
    assert (star, sub, ss) == ("Ketu", "Ketu", "Venus")


@pytest.mark.parametrize("longitude", [0.0, 13.3333, 30.0, 90.0, 180.0, 359.999])
def test_kp_lords_are_valid(longitude: float) -> None:
    """All three returned lords must always be one of the nine Vimshottari lords."""
    valid = set(ve.DASHA_ORDER)
    star, sub, ss = ve.kp_sublord(longitude)
    assert star in valid
    assert sub in valid
    assert ss in valid
