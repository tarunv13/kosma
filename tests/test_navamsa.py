"""D9 (Navamsa) tests against the Parashari rule."""

from __future__ import annotations

import pytest

from kosma import vedic_engine as ve


@pytest.mark.parametrize(
    "longitude,expected_sign",
    [
        # Aries 0 deg -> 1st navamsa of Aries -> Aries
        (0.0, "Aries"),
        # Aries 3 deg 21' is just inside the 2nd navamsa -> Taurus
        (3.5, "Taurus"),
        # Aries 30 deg (Taurus 0 deg) -> 1st navamsa of Taurus -> Capricorn
        (30.0, "Capricorn"),
        # Gemini 0 deg -> 1st navamsa of Gemini (dual air) -> Libra
        (60.0, "Libra"),
        # Cancer 0 deg -> Cancer
        (90.0, "Cancer"),
        # Leo 0 deg -> 1st navamsa of Leo (fixed fire) -> Aries
        (120.0, "Aries"),
        # Virgo 0 deg (dual earth) -> Capricorn
        (150.0, "Capricorn"),
        # Libra 0 deg (movable air) -> Libra
        (180.0, "Libra"),
        # Scorpio 0 deg (fixed water) -> Cancer
        (210.0, "Cancer"),
        # Sagittarius 0 deg (dual fire) -> Aries
        (240.0, "Aries"),
        # Capricorn 0 deg (movable earth) -> Capricorn
        (270.0, "Capricorn"),
        # Aquarius 0 deg (fixed air) -> Libra
        (300.0, "Libra"),
        # Pisces 0 deg (dual water) -> Cancer
        (330.0, "Cancer"),
        # Pisces 29 deg 59'59" -> last navamsa of Pisces -> Pisces
        (359.99, "Pisces"),
    ],
)
def test_navamsa_first_navamsa_per_sign(longitude: float, expected_sign: str) -> None:
    idx = ve.navamsa_sign_idx(longitude)
    assert ve.SIGNS[idx] == expected_sign


def test_navamsa_chart_returns_all_planets_plus_ascendant(reference_chart: ve.Chart) -> None:
    nav = ve.navamsa_chart(reference_chart)
    assert "__asc__" in nav
    for name in ve.VEDIC_PLANETS:
        assert name in nav
        assert nav[name].sign in ve.SIGNS
        assert 1 <= nav[name].house <= 12


def test_navamsa_houses_are_consistent(reference_chart: ve.Chart) -> None:
    """Houses are derived from the D9 ascendant; D9 ascendant must always be H1."""
    nav = ve.navamsa_chart(reference_chart)
    asc_sign = nav["__asc__"].sign
    asc_idx = ve.SIGNS.index(asc_sign)
    for name in ve.VEDIC_PLANETS:
        body_idx = ve.SIGNS.index(nav[name].sign)
        expected_house = ((body_idx - asc_idx) % 12) + 1
        assert nav[name].house == expected_house
