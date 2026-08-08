"""Yoga detection and the divisional charts."""

from __future__ import annotations

import pytest

from kosma import vargas as vg
from kosma import vedic_engine as ve
from kosma import yogas as yg

ALL_CHART_FIXTURES = ("reference_chart", "second_chart")


# ── yogas ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("fixture", ALL_CHART_FIXTURES)
def test_every_yoga_is_sourced_and_explained(fixture: str, request) -> None:
    chart = request.getfixturevalue(fixture)
    for y in yg.detect_yogas(chart).formed:
        assert y.rule.strip(), f"{y.name} has no rule"
        assert y.source.strip(), f"{y.name} has no source"
        assert y.detail.strip(), f"{y.name} does not say how it formed"
        assert y.planets, f"{y.name} names no planets"
        assert y.polarity in (-1, 0, 1)


def test_kala_sarpa_is_flagged_as_non_classical() -> None:
    """It is widely quoted and has no classical source; the pack must say so."""
    # A chart with every planet on one side of the nodal axis.
    chart = ve.build_chart(
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
    detected = [y for y in yg.detect_yogas(chart).formed if "Kala Sarpa" in y.name]
    for y in detected:
        assert y.disputed is True
        assert "Not found in" in y.source


def test_reference_chart_forms_neechabhanga(reference_chart: ve.Chart) -> None:
    """Saturn is debilitated in Aries, and its debility is cancelled."""
    formed = yg.detect_yogas(reference_chart).formed
    nb = [y for y in formed if y.name == "Neechabhanga Raja Yoga"]
    assert nb, "a debilitated Saturn with a cancelling condition should form it"
    assert "Saturn" in nb[0].planets
    assert "cancellation holds because" in nb[0].detail


def test_reference_chart_forms_gajakesari(reference_chart: ve.Chart) -> None:
    names = [y.name for y in yg.detect_yogas(reference_chart).formed]
    assert "Gajakesari Yoga" in names


def test_reference_chart_forms_budhaditya(reference_chart: ve.Chart) -> None:
    names = [y.name for y in yg.detect_yogas(reference_chart).formed]
    assert "Budhaditya Yoga" in names


def test_no_duplicate_yogas(reference_chart: ve.Chart, second_chart: ve.Chart) -> None:
    for chart in (reference_chart, second_chart):
        seen = [(y.name, tuple(sorted(y.planets))) for y in yg.detect_yogas(chart).formed]
        assert len(seen) == len(set(seen))


def test_lunar_yogas_are_mutually_exclusive(
    reference_chart: ve.Chart, second_chart: ve.Chart
) -> None:
    """Sunapha, Anapha, Durudhara and Kemadruma partition the same condition."""
    exclusive = {"Sunapha Yoga", "Anapha Yoga", "Durudhara Yoga", "Kemadruma Yoga"}
    for chart in (reference_chart, second_chart):
        names = [y.name for y in yg.detect_yogas(chart).formed if y.name in exclusive]
        assert len(names) <= 1, f"got {names}"


def test_disputed_yogas_are_excluded_from_the_helpers(reference_chart: ve.Chart) -> None:
    report = yg.detect_yogas(reference_chart)
    for y in report.auspicious + report.challenging:
        assert not y.disputed
    for y in report.flagged:
        assert y.disputed


# ── vargas ────────────────────────────────────────────────────────────


def test_all_sixteen_vargas_build(reference_chart: ve.Chart) -> None:
    charts = vg.build_all_vargas(reference_chart)
    assert len(charts) == 16
    for code, v in charts.items():
        assert v.code == code
        assert v.ascendant_sign in ve.SIGNS
        assert set(v.positions) == set(ve.VEDIC_PLANETS)
        for pos in v.positions.values():
            assert 1 <= pos.house <= 12
            assert pos.sign in ve.SIGNS


def test_d1_is_the_rasi_chart(reference_chart: ve.Chart) -> None:
    d1 = vg.build_varga(reference_chart, "D1")
    assert d1.ascendant_sign == reference_chart.ascendant_sign
    for name in ve.VEDIC_PLANETS:
        assert d1.positions[name].sign == reference_chart.planets[name].sign
        assert d1.positions[name].house == reference_chart.planets[name].house


def test_d9_matches_the_original_navamsa_implementation(reference_chart: ve.Chart) -> None:
    """The generalised engine must not have changed the shipped D9."""
    original = ve.navamsa_chart(reference_chart)
    d9 = vg.build_varga(reference_chart, "D9")
    assert d9.ascendant_sign == original["__asc__"].sign
    for name in ve.VEDIC_PLANETS:
        assert d9.positions[name].sign == original[name].sign
        assert d9.positions[name].house == original[name].house


@pytest.mark.parametrize("sign_idx", range(12))
def test_hora_only_ever_yields_cancer_or_leo(sign_idx: int) -> None:
    for deg in (0.0, 14.9, 15.0, 29.9):
        assert vg.d2(sign_idx, deg) in (3, 4)


@pytest.mark.parametrize("sign_idx", range(12))
def test_trimsamsa_never_lands_in_a_luminary_sign(sign_idx: int) -> None:
    """The Sun and Moon rule no trimsamsa, so Cancer and Leo cannot appear."""
    for deg in [d * 0.5 for d in range(60)]:
        assert vg.d30(sign_idx, deg) not in (3, 4)


@pytest.mark.parametrize("spec", vg.VARGAS, ids=lambda s: s.code)
def test_varga_functions_stay_in_range(spec: vg.VargaSpec) -> None:
    for sign_idx in range(12):
        for deg in [d * 0.25 for d in range(120)]:
            assert 0 <= spec.fn(sign_idx, deg) <= 11


def test_vargottama_is_consistent_with_d9(reference_chart: ve.Chart) -> None:
    d9 = vg.build_varga(reference_chart, "D9")
    for name in ve.VEDIC_PLANETS:
        expected = d9.positions[name].sign == reference_chart.planets[name].sign
        assert vg.vargottama(reference_chart, name) is expected


def test_varga_dignity_count_is_bounded(reference_chart: ve.Chart) -> None:
    for name in ve.VEDIC_PLANETS:
        tally = vg.varga_dignity_count(reference_chart, name)
        assert tally["total"] == len(vg.SAPTAVARGA)
        assert tally["strong_count"] + tally["weak_count"] <= tally["total"]
