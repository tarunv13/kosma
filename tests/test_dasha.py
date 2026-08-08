"""Vimshottari dasha tests."""

from __future__ import annotations

from kosma import vedic_engine as ve


def test_dasha_total_length_is_120_years(reference_chart: ve.Chart) -> None:
    """The 9-dasha cycle must sum to 120 years."""
    moon_lon = reference_chart.planets["Moon"].longitude
    birth_jd = reference_chart.jd
    dashas = ve.vimshottari_dasha(moon_lon, birth_jd)

    # Take the second cycle (a full 120 years) starting after the partial first.
    # Skip the first (partial) dasha, take the next 9 lords.
    full_cycle = dashas[1:10]
    total_days = full_cycle[-1][2] - full_cycle[0][1]
    total_years = total_days / 365.25
    assert abs(total_years - 120.0) < 0.5


def test_dasha_lords_cycle_in_order(reference_chart: ve.Chart) -> None:
    """The mahadasha sequence must follow the canonical Vimshottari order."""
    moon_lon = reference_chart.planets["Moon"].longitude
    birth_jd = reference_chart.jd
    dashas = ve.vimshottari_dasha(moon_lon, birth_jd)

    first_lord = dashas[0][0]
    expected_idx = ve.DASHA_ORDER.index(first_lord)
    for offset, (lord, _, _) in enumerate(dashas[:18]):
        assert lord == ve.DASHA_ORDER[(expected_idx + offset) % 9]


def test_current_periods_resolves_at_birth(reference_chart: ve.Chart) -> None:
    """At the moment of birth, the active mahadasha is the one that contains it."""
    moon_lon = reference_chart.planets["Moon"].longitude
    birth_jd = reference_chart.jd
    dashas = ve.vimshottari_dasha(moon_lon, birth_jd)

    maha, antar, prat = ve.current_periods(dashas, birth_jd)
    assert maha is not None
    assert antar is not None
    assert prat is not None
    assert maha[1] <= birth_jd < maha[2]
    assert antar[1] <= birth_jd < antar[2]
    assert prat[1] <= birth_jd < prat[2]


def test_first_dasha_lord_matches_moon_nakshatra_lord(reference_chart: ve.Chart) -> None:
    """The first mahadasha lord at birth equals the lord of the Moon's nakshatra."""
    moon = reference_chart.planets["Moon"]
    dashas = ve.vimshottari_dasha(moon.longitude, reference_chart.jd)
    assert dashas[0][0] == moon.nak_lord
