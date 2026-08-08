"""Compatibility: koota tables, doshas, synastry, and the shared gate."""

from __future__ import annotations

import itertools

import pytest

from kosma import compatibility as cp
from kosma import vedic_engine as ve


@pytest.fixture(scope="module")
def pa(reference_chart: ve.Chart) -> cp.Person:
    return cp.Person(label="A", chart=reference_chart)


@pytest.fixture(scope="module")
def pb(second_chart: ve.Chart) -> cp.Person:
    return cp.Person(label="B", chart=second_chart)


@pytest.fixture(scope="module")
def pc() -> cp.Person:
    return cp.Person(
        label="C",
        chart=ve.build_chart(
            label="C",
            year=1995,
            month=3,
            day=21,
            hour=18,
            minute=0,
            lat=28.6139,
            lon_geo=77.2090,
            tz=5.5,
        ),
    )


# ── reference tables ──────────────────────────────────────────────────


def test_ashtakoota_maxima_sum_to_36(pa: cp.Person, pb: cp.Person) -> None:
    milan = cp.guna_milan(pa, pb)
    assert milan.maximum == 36.0
    assert len(milan.kootas) == 8


def test_nadi_partitions_all_27_nakshatras_exactly_once() -> None:
    combined = cp._NADI_ADI + cp._NADI_MADHYA + cp._NADI_ANTYA
    assert sorted(combined) == list(range(27))
    assert len(cp._NADI_ADI) == len(cp._NADI_MADHYA) == len(cp._NADI_ANTYA) == 9


def test_yoni_enemy_pairs_cover_every_animal_once() -> None:
    from kosma.nakshatras import NAKSHATRA_TABLE

    animals = {n.yoni for n in NAKSHATRA_TABLE.values()}
    assert len(animals) == 14
    paired = [a for pair in cp._YONI_ENEMIES for a in pair]
    assert sorted(paired) == sorted(animals)
    assert len(paired) == len(set(paired)), "no animal may appear in two enemy pairs"


def test_vashya_groups_resolve_for_every_sign() -> None:
    groups = set()
    for sign_idx in range(12):
        for deg in (0.0, 14.9, 15.0, 29.9):
            groups.add(cp._vashya_group(sign_idx, deg))
    assert groups == {"chatushpada", "manava", "jalachara", "vanachara", "keeta"}


def test_vashya_score_table_covers_every_group_pairing() -> None:
    groups = ("chatushpada", "manava", "jalachara", "vanachara", "keeta")
    for a, b in itertools.combinations_with_replacement(groups, 2):
        assert frozenset({a, b}) in cp._VASHYA_SCORES, f"missing {a}/{b}"


def test_gana_and_maitri_tables_are_complete() -> None:
    for a, b in itertools.combinations_with_replacement(("deva", "manushya", "rakshasa"), 2):
        assert frozenset({a, b}) in cp._GANA_SCORES
    for a, b in itertools.combinations_with_replacement(("friend", "neutral", "enemy"), 2):
        assert frozenset({a, b}) in cp._MAITRI_SCORES


# ── koota behaviour ───────────────────────────────────────────────────


def test_every_koota_stays_within_its_range(pa: cp.Person, pb: cp.Person, pc: cp.Person) -> None:
    for x, y in itertools.permutations((pa, pb, pc), 2):
        for k in cp.guna_milan(x, y).kootas:
            assert 0.0 <= k.score <= k.maximum, f"{k.name} out of range"
            assert k.detail and k.rule and k.source


def test_symmetric_kootas_do_not_depend_on_order(pa: cp.Person, pb: cp.Person) -> None:
    """Only Varna is directional; the rest must give the same score either way."""
    forward = {k.name: k.score for k in cp.guna_milan(pa, pb).kootas}
    reverse = {k.name: k.score for k in cp.guna_milan(pb, pa).kootas}
    for name in ("Vashya", "Tara", "Yoni", "Graha Maitri", "Gana", "Bhakoot", "Nadi"):
        assert forward[name] == reverse[name], f"{name} changed when the order flipped"


def test_varna_is_directional_and_says_so(pa: cp.Person, pb: cp.Person) -> None:
    forward = next(k for k in cp.guna_milan(pa, pb).kootas if k.name == "Varna")
    reverse = next(k for k in cp.guna_milan(pb, pa).kootas if k.name == "Varna")
    # Whichever way round, at least one direction scores the point.
    assert forward.score + reverse.score >= 1.0
    note = forward.variant_note or ""
    assert "directional" in note, "the asymmetry must be disclosed"
    assert "birth caste" in note, "varna must be distinguished from social caste"


def test_identical_charts_score_near_the_maximum(reference_chart: ve.Chart) -> None:
    """Someone compared with themselves shares every Moon-derived factor.

    Nadi and Bhakoot both void on an identical chart, which is exactly what
    the classical rule says and a useful sanity check that they are wired the
    right way round.
    """
    twin_a = cp.Person(label="X", chart=reference_chart)
    twin_b = cp.Person(label="Y", chart=reference_chart)
    milan = cp.guna_milan(twin_a, twin_b)
    by_name = {k.name: k for k in milan.kootas}
    assert by_name["Varna"].score == 1.0
    assert by_name["Vashya"].full
    assert by_name["Yoni"].full
    assert by_name["Gana"].full
    assert by_name["Graha Maitri"].full
    assert by_name["Nadi"].void, "same nakshatra means same nadi, which voids"
    assert by_name["Bhakoot"].full, "1/1 is not one of the voiding distances"


def test_tara_is_computed_both_ways(pa: cp.Person, pb: cp.Person) -> None:
    k = next(k for k in cp.guna_milan(pa, pb).kootas if k.name == "Tara")
    assert k.score in (0.0, 1.5, 3.0)
    assert "and back gives" in k.detail


# ── doshas ────────────────────────────────────────────────────────────


def test_mangal_dosha_reports_its_references(pa: cp.Person) -> None:
    d = cp.mangal_dosha(pa)
    assert d.name == "Mangal dosha"
    assert d.status in ("absent", "present but cancelled", "present, no cancellation found")
    assert "not a disqualification" in d.note


def test_mutual_mangal_cancels_when_both_carry_it(pa: cp.Person, pb: cp.Person) -> None:
    d = cp.mutual_mangal(pa, pb)
    both = cp.mangal_dosha(pa).present and cp.mangal_dosha(pb).present
    if both:
        assert d.cancelled
        assert "mutually cancelling" in " ".join(d.cancellations)


def test_voided_kootas_raise_the_matching_dosha(pa: cp.Person, pb: cp.Person) -> None:
    by_name = {k.name: k for k in cp.guna_milan(pa, pb).kootas}
    assert cp.bhakoot_dosha(pa, pb, by_name["Bhakoot"]).present is by_name["Bhakoot"].void
    assert cp.nadi_dosha(pa, pb, by_name["Nadi"]).present is by_name["Nadi"].void


# ── synastry ──────────────────────────────────────────────────────────


def test_overlays_place_every_planet(pa: cp.Person, pb: cp.Person) -> None:
    ov = cp.overlays(pa, pb)
    assert len(ov) == len(ve.VEDIC_PLANETS)
    assert {o.planet for o in ov} == set(ve.VEDIC_PLANETS)
    for o in ov:
        assert 1 <= o.into_house <= 12
        assert o.theme


def test_overlays_are_not_symmetric(pa: cp.Person, pb: cp.Person) -> None:
    ab = {o.planet: o.into_house for o in cp.overlays(pa, pb)}
    ba = {o.planet: o.into_house for o in cp.overlays(pb, pa)}
    assert ab != ba, "overlays are read from each lagna and should differ"


def test_cross_aspects_never_use_nodal_drishti(pa: cp.Person, pb: cp.Person) -> None:
    for ca in cp.cross_aspects(pa, pb) + cp.cross_aspects(pb, pa):
        assert ca.source_planet not in ("Rahu", "Ketu")


def test_dasha_sync_reads_both_charts(pa: cp.Person, pb: cp.Person, pinned_now_jd: float) -> None:
    s = cp.dasha_sync(pa, pb, pinned_now_jd)
    assert s.a_maha and s.b_maha
    assert s.relation in ("same lord", "friend", "neutral", "enemy")
    assert s.polarity in (-1, 0, 1)


# ── modes and the gate ────────────────────────────────────────────────


def test_relationship_mode_uses_all_eight(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    r = cp.compare(pa, pb, pinned_now_jd, "relationship")
    assert r.milan.maximum == 36.0
    assert {k.name for k in r.milan.kootas} >= {"Yoni", "Nadi", "Varna"}


def test_friendship_mode_drops_the_marriage_kootas(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    r = cp.compare(pa, pb, pinned_now_jd, "friendship")
    names = {k.name for k in r.milan.kootas}
    assert "Yoni" not in names, "Yoni assesses sexual compatibility; irrelevant to friendship"
    assert "Nadi" not in names, "Nadi assesses genetic compatibility; irrelevant to friendship"
    assert "Varna" not in names
    assert names == {"Vashya", "Tara", "Graha Maitri", "Gana", "Bhakoot"}


def test_friendship_scheme_admits_it_is_not_classical(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    r = cp.compare(pa, pb, pinned_now_jd, "friendship")
    assert "not a classical named scheme" in r.milan.critique


def test_ashtakoota_critique_is_attached(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    r = cp.compare(pa, pb, pinned_now_jd, "relationship")
    assert "eight factors" in r.milan.critique
    assert "not a verdict" in r.milan.critique


def test_unknown_mode_is_rejected(pa: cp.Person, pb: cp.Person, pinned_now_jd: float) -> None:
    with pytest.raises(ValueError):
        cp.compare(pa, pb, pinned_now_jd, "marriage")


def test_every_topic_is_reported_or_withheld(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    for mode, topics in (
        ("relationship", cp.RELATIONSHIP_TOPICS),
        ("friendship", cp.FRIENDSHIP_TOPICS),
    ):
        r = cp.compare(pa, pb, pinned_now_jd, mode)
        seen = {t.topic for t in r.findings} | {t.topic for t in r.withheld}
        assert seen == set(topics)


def test_findings_clear_the_shared_threshold(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    from kosma.evidence import MIN_DISTINCT_KINDS

    r = cp.compare(pa, pb, pinned_now_jd, "relationship")
    for f in r.findings:
        assert len(f.outcome.kinds) >= MIN_DISTINCT_KINDS
    for w in r.withheld:
        assert not w.outcome.passed


def test_compatibility_evidence_is_sourced(
    pa: cp.Person, pb: cp.Person, pinned_now_jd: float
) -> None:
    r = cp.compare(pa, pb, pinned_now_jd, "relationship")
    assert r.ledger
    ids = [e.id for e in r.ledger]
    assert len(ids) == len(set(ids))
    for e in r.ledger:
        assert e.kind in cp.COMPAT_FACTOR_KINDS
        assert e.statement and e.basis and e.source


def test_group_compares_every_pair(
    pa: cp.Person, pb: cp.Person, pc: cp.Person, pinned_now_jd: float
) -> None:
    g = cp.compare_group([pa, pb, pc], pinned_now_jd, "friendship")
    assert len(g.pairs) == 3
    assert {frozenset((p.a, p.b)) for p in g.pairs} == {
        frozenset(("A", "B")),
        frozenset(("A", "C")),
        frozenset(("B", "C")),
    }
    assert g.pair("A", "C") is not None
    assert g.pair("A", "Z") is None


def test_group_needs_at_least_two(pa: cp.Person, pinned_now_jd: float) -> None:
    with pytest.raises(ValueError):
        cp.compare_group([pa], pinned_now_jd)
