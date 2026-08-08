"""Engine smoke tests against the reference chart.

The reference is the **J2000.0 epoch** — 1 January 2000, 12:00 UT, London
(51.5074 N, 0.1278 W). A synthetic astronomical instant, chosen precisely
because it is not anybody's birth: pinning a public test suite to a real
person's birth data would publish that data, which is the one thing this
project claims not to do.

Every value below is independently re-verifiable in any Vedic software set to
Lahiri ayanamsa, which is all a reference chart was ever for.
"""

from __future__ import annotations

import pytest

from kosma import vedic_engine as ve


def test_ascendant_matches_reference(reference_chart: ve.Chart) -> None:
    assert reference_chart.ascendant_sign == "Aries"
    assert reference_chart.ascendant_nak == "Ashwini"
    assert reference_chart.ascendant_pada == 1
    # 0 deg 09' 40.9"
    assert reference_chart.ascendant_deg == pytest.approx(0.161, abs=0.05)
    # KP chain
    assert reference_chart.ascendant_kp == ("Ketu", "Ketu", "Venus")


@pytest.mark.parametrize(
    "name,sign,house,nakshatra",
    [
        ("Sun", "Sagittarius", 9, "Purva Ashadha"),
        ("Moon", "Libra", 7, "Swati"),
        ("Mars", "Aquarius", 11, "Dhanishtha"),
        ("Mercury", "Sagittarius", 9, "Moola"),
        ("Jupiter", "Aries", 1, "Ashwini"),
        ("Venus", "Scorpio", 8, "Anuradha"),
        ("Saturn", "Aries", 1, "Bharani"),
        ("Rahu", "Cancer", 4, "Pushya"),
        ("Ketu", "Capricorn", 10, "Shravana"),
    ],
)
def test_planet_placements(
    reference_chart: ve.Chart, name: str, sign: str, house: int, nakshatra: str
) -> None:
    p = reference_chart.planets[name]
    assert p.sign == sign, f"{name} expected sign {sign}, got {p.sign}"
    assert p.house == house, f"{name} expected house {house}, got {p.house}"
    assert p.nakshatra == nakshatra, f"{name} expected nakshatra {nakshatra}, got {p.nakshatra}"


def test_saturn_alone_is_retrograde(reference_chart: ve.Chart) -> None:
    """Saturn was the only retrograde graha at the J2000 epoch."""
    retrograde = [n for n in ve.VEDIC_PLANETS if reference_chart.planets[n].retrograde]
    assert retrograde == ["Saturn"]


def test_nodes_oppose_each_other(reference_chart: ve.Chart) -> None:
    """Rahu and Ketu must be exactly 180 deg apart by construction."""
    rahu = reference_chart.planets["Rahu"].longitude
    ketu = reference_chart.planets["Ketu"].longitude
    diff = abs((rahu - ketu) % 360 - 180)
    assert diff < 0.0001


def test_jaimini_karakas(reference_chart: ve.Chart) -> None:
    karakas = ve.jaimini_karakas(reference_chart)
    assert karakas["Atmakaraka"] == "Moon"
    assert karakas["Darakaraka"] == "Jupiter"
    # 7 distinct planets
    assert len(set(karakas.values())) == 7


def test_panchanga_shape(reference_chart: ve.Chart) -> None:
    p = ve.panchanga_for(reference_chart)
    assert p.vara in {
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    }
    assert p.paksha in {"Shukla", "Krishna"}
    assert p.tithi in ve.TITHI_NAMES
    assert p.yoga in ve.YOGA_NAMES
    assert p.karana in ve.KARANA_NAMES
    assert 1 <= p.moon_pada <= 4
    assert 0 <= p.sun_moon_diff < 360
