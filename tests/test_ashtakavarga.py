"""Ashtakavarga tables and totals.

The BPHS row totals are the best available check that the benefic-place tables
were transcribed correctly: get one cell wrong and a total moves.
"""

from __future__ import annotations

import pytest

from kosma import ashtakavarga as av
from kosma import vedic_engine as ve


@pytest.mark.parametrize("planet,expected", sorted(av.EXPECTED_TOTALS.items()))
def test_benefic_place_tables_match_bphs_totals(planet: str, expected: int) -> None:
    total = sum(len(places) for places in av.BENEFIC_PLACES[planet].values())
    assert total == expected, f"{planet} table sums to {total}, expected {expected}"


def test_all_tables_have_all_eight_contributors() -> None:
    for planet, table in av.BENEFIC_PLACES.items():
        assert tuple(table) == av.CONTRIBUTORS, f"{planet} is missing a contributor"


def test_benefic_places_are_valid_house_numbers() -> None:
    for planet, table in av.BENEFIC_PLACES.items():
        for contributor, places in table.items():
            assert len(set(places)) == len(places), f"{planet}/{contributor} repeats a house"
            assert all(1 <= h <= 12 for h in places), f"{planet}/{contributor} out of range"


def test_computed_bhinna_totals_match_the_tables(reference_chart: ve.Chart) -> None:
    report = av.compute_ashtakavarga(reference_chart)
    for planet, expected in av.EXPECTED_TOTALS.items():
        assert report.bhinna[planet].total == expected


def test_sarvashtakavarga_totals_337(reference_chart: ve.Chart, second_chart: ve.Chart) -> None:
    for chart in (reference_chart, second_chart):
        report = av.compute_ashtakavarga(chart)
        assert report.sarva_total == av.SARVA_TOTAL
        assert sum(report.sarva_by_house().values()) == av.SARVA_TOTAL


def test_sarva_by_house_is_a_rotation_of_by_sign(reference_chart: ve.Chart) -> None:
    report = av.compute_ashtakavarga(reference_chart)
    by_house = report.sarva_by_house()
    asc = reference_chart.ascendant_sign_idx
    for h in range(1, 13):
        assert by_house[h] == report.sarva_by_sign[(asc + h - 1) % 12]


def test_charts_differ(reference_chart: ve.Chart, second_chart: ve.Chart) -> None:
    """A constant would also pass the totals test; the distributions must differ."""
    a = av.compute_ashtakavarga(reference_chart).sarva_by_sign
    b = av.compute_ashtakavarga(second_chart).sarva_by_sign
    assert a != b


def test_strong_and_weak_houses_respect_thresholds(reference_chart: ve.Chart) -> None:
    report = av.compute_ashtakavarga(reference_chart)
    by_house = report.sarva_by_house()
    for h in report.strong_houses():
        assert by_house[h] >= av.SAV_RICH
    for h in report.weak_houses():
        assert by_house[h] <= av.SAV_POOR


def test_transit_bindus_are_none_for_nodes(reference_chart: ve.Chart) -> None:
    report = av.compute_ashtakavarga(reference_chart)
    assert av.transit_bindus(report, "Rahu", 0) is None
    assert av.transit_bindus(report, "Saturn", 0) is not None
