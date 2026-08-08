"""
Ashtakavarga — the eight-source benefic point system.

For each of the seven planets, eight contributors (the seven planets plus the
lagna) each donate a benefic point to a fixed set of houses counted from
themselves. Summing the donations gives that planet's Bhinnashtakavarga; summing
all seven Bhinna charts gives the Sarvashtakavarga.

The tables below are the BPHS ones. Their row totals are a useful self-check
and are asserted in the test suite: Sun 48, Moon 49, Mars 39, Mercury 54,
Jupiter 56, Venus 52, Saturn 39, summing to 337 across the Sarvashtakavarga.

Source
------
* Brihat Parashara Hora Shastra ch. 66-70 (Ashtakavarga).
"""

from __future__ import annotations

from dataclasses import dataclass

from .vedic_engine import SIGNS, Chart

CONTRIBUTORS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna")
BAV_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# benefic_places[planet][contributor] -> houses counted from the contributor
BENEFIC_PLACES: dict[str, dict[str, tuple[int, ...]]] = {
    "Sun": {
        "Sun": (1, 2, 4, 7, 8, 9, 10, 11),
        "Moon": (3, 6, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (5, 6, 9, 11),
        "Venus": (6, 7, 12),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna": (3, 4, 6, 10, 11, 12),
    },
    "Moon": {
        "Sun": (3, 6, 7, 8, 10, 11),
        "Moon": (1, 3, 6, 7, 10, 11),
        "Mars": (2, 3, 5, 6, 9, 10, 11),
        "Mercury": (1, 3, 4, 5, 7, 8, 10, 11),
        "Jupiter": (1, 4, 7, 8, 10, 11, 12),
        "Venus": (3, 4, 5, 7, 9, 10, 11),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (3, 6, 10, 11),
    },
    "Mars": {
        "Sun": (3, 5, 6, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (3, 5, 6, 11),
        "Jupiter": (6, 10, 11, 12),
        "Venus": (6, 8, 11, 12),
        "Saturn": (1, 4, 7, 8, 9, 10, 11),
        "Lagna": (1, 3, 6, 10, 11),
    },
    "Mercury": {
        "Sun": (5, 6, 9, 11, 12),
        "Moon": (2, 4, 6, 8, 10, 11),
        "Mars": (1, 2, 4, 7, 8, 9, 10, 11),
        "Mercury": (1, 3, 5, 6, 9, 10, 11, 12),
        "Jupiter": (6, 8, 11, 12),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 11),
        "Saturn": (1, 2, 4, 7, 8, 9, 10, 11),
        "Lagna": (1, 2, 4, 6, 8, 10, 11),
    },
    "Jupiter": {
        "Sun": (1, 2, 3, 4, 7, 8, 9, 10, 11),
        "Moon": (2, 5, 7, 9, 11),
        "Mars": (1, 2, 4, 7, 8, 10, 11),
        "Mercury": (1, 2, 4, 5, 6, 9, 10, 11),
        "Jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
        "Venus": (2, 5, 6, 9, 10, 11),
        "Saturn": (3, 5, 6, 12),
        "Lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11),
    },
    "Venus": {
        "Sun": (8, 11, 12),
        "Moon": (1, 2, 3, 4, 5, 8, 9, 11, 12),
        "Mars": (3, 5, 6, 9, 11, 12),
        "Mercury": (3, 5, 6, 9, 11),
        "Jupiter": (5, 8, 9, 10, 11),
        "Venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
        "Saturn": (3, 4, 5, 8, 9, 10, 11),
        "Lagna": (1, 2, 3, 4, 5, 8, 9, 11),
    },
    "Saturn": {
        "Sun": (1, 2, 4, 7, 8, 10, 11),
        "Moon": (3, 6, 11),
        "Mars": (3, 5, 6, 10, 11, 12),
        "Mercury": (6, 8, 9, 10, 11, 12),
        "Jupiter": (5, 6, 11, 12),
        "Venus": (6, 11, 12),
        "Saturn": (3, 5, 6, 11),
        "Lagna": (1, 3, 4, 6, 10, 11),
    },
}

# Expected row totals, used as a self-check (BPHS).
EXPECTED_TOTALS: dict[str, int] = {
    "Sun": 48,
    "Moon": 49,
    "Mars": 39,
    "Mercury": 54,
    "Jupiter": 56,
    "Venus": 52,
    "Saturn": 39,
}
SARVA_TOTAL = 337

# Interpretive thresholds are classical rules of thumb, not predictions.
SAV_RICH = 30  # a sign carrying 30+ points is classically "strong"
SAV_POOR = 25  # 25 or fewer is classically "weak"


@dataclass(frozen=True)
class Bhinna:
    """One planet's ashtakavarga across the twelve signs."""

    planet: str
    points_by_sign: tuple[int, ...]  # index 0 = Aries
    total: int

    def in_sign(self, sign_idx: int) -> int:
        return self.points_by_sign[sign_idx % 12]


@dataclass(frozen=True)
class AshtakavargaReport:
    bhinna: dict[str, Bhinna]
    sarva_by_sign: tuple[int, ...]
    sarva_total: int
    ascendant_sign_idx: int

    def sarva_in_house(self, house: int) -> int:
        """Sarvashtakavarga points on a whole-sign house from the lagna."""
        return self.sarva_by_sign[(self.ascendant_sign_idx + house - 1) % 12]

    def sarva_by_house(self) -> dict[int, int]:
        return {h: self.sarva_in_house(h) for h in range(1, 13)}

    def bindus_for(self, planet: str) -> int:
        """Points a planet carries in the sign it actually occupies."""
        return self.bhinna[planet].total

    def strong_houses(self) -> list[int]:
        return [h for h, v in self.sarva_by_house().items() if v >= SAV_RICH]

    def weak_houses(self) -> list[int]:
        return [h for h, v in self.sarva_by_house().items() if v <= SAV_POOR]


def compute_ashtakavarga(chart: Chart) -> AshtakavargaReport:
    """Build the full Bhinna and Sarva ashtakavarga for a chart."""
    positions: dict[str, int] = {p: chart.planets[p].sign_idx for p in BAV_PLANETS}
    positions["Lagna"] = chart.ascendant_sign_idx

    bhinna: dict[str, Bhinna] = {}
    for planet in BAV_PLANETS:
        points = [0] * 12
        for contributor in CONTRIBUTORS:
            base = positions[contributor]
            for house in BENEFIC_PLACES[planet][contributor]:
                points[(base + house - 1) % 12] += 1
        bhinna[planet] = Bhinna(
            planet=planet,
            points_by_sign=tuple(points),
            total=sum(points),
        )

    sarva = tuple(sum(bhinna[p].points_by_sign[i] for p in BAV_PLANETS) for i in range(12))
    return AshtakavargaReport(
        bhinna=bhinna,
        sarva_by_sign=sarva,
        sarva_total=sum(sarva),
        ascendant_sign_idx=chart.ascendant_sign_idx,
    )


def own_bindus(chart: Chart, report: AshtakavargaReport, planet: str) -> int | None:
    """Points a planet's own ashtakavarga gives to the sign it occupies.

    This is the figure used when judging whether a transit through that sign
    will deliver: classically, four or more of a planet's own bindus in the
    sign it transits is treated as supportive, and three or fewer as not.
    """
    if planet not in BAV_PLANETS:
        return None
    return report.bhinna[planet].in_sign(chart.planets[planet].sign_idx)


def transit_bindus(report: AshtakavargaReport, planet: str, transit_sign_idx: int) -> int | None:
    """Points a planet carries in a sign it is currently transiting."""
    if planet not in BAV_PLANETS:
        return None
    return report.bhinna[planet].in_sign(transit_sign_idx)


def describe_sign(report: AshtakavargaReport, sign_idx: int) -> str:
    value = report.sarva_by_sign[sign_idx % 12]
    if value >= SAV_RICH:
        band = "well supplied"
    elif value <= SAV_POOR:
        band = "thinly supplied"
    else:
        band = "average"
    return f"{SIGNS[sign_idx % 12]} carries {value} sarvashtakavarga points ({band})"
