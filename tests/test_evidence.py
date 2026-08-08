"""The confirmation gate.

This is the module that decides what the system is allowed to say, so these
tests are about the gate's arithmetic rather than about astrology.
"""

from __future__ import annotations

from kosma import evidence as ev
from kosma import vedic_engine as ve


def _report(chart: ve.Chart, now_jd: float) -> ev.EvidenceReport:
    return ev.build_evidence(chart, chart.jd, now_jd)


def test_every_house_is_either_reported_or_withheld(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    r = _report(reference_chart, pinned_now_jd)
    houses = {f.house for f in r.findings} | {w.house for w in r.withheld}
    assert houses == set(range(1, 13))
    assert len(r.findings) + len(r.withheld) == 12


def test_findings_meet_the_threshold(reference_chart: ve.Chart, pinned_now_jd: float) -> None:
    r = _report(reference_chart, pinned_now_jd)
    for f in r.findings:
        assert len(f.distinct_kinds) >= ev.MIN_DISTINCT_KINDS, f.statement


def test_withheld_entries_explain_themselves(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    r = _report(reference_chart, pinned_now_jd)
    for w in r.withheld:
        assert str(ev.MIN_DISTINCT_KINDS) in w.reason
        assert w.topic
        assert w.evidence, "withheld topics still carry their evidence for audit"


def test_gate_actually_withholds_somewhere(
    reference_chart: ve.Chart, second_chart: ve.Chart, pinned_now_jd: float
) -> None:
    """A gate that never fires is decoration, not a constraint."""
    withheld = 0
    for chart in (reference_chart, second_chart):
        withheld += len(_report(chart, pinned_now_jd).withheld)
    assert withheld > 0


def test_disputed_evidence_never_satisfies_the_gate(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    r = _report(reference_chart, pinned_now_jd)
    for f in r.findings:
        counted = {e.kind for e in f.evidence if not e.disputed}
        for kind in f.distinct_kinds:
            assert kind in counted, f"{kind} was credited but only appears in disputed evidence"


def test_nodal_aspects_are_marked_disputed(reference_chart: ve.Chart, pinned_now_jd: float) -> None:
    r = _report(reference_chart, pinned_now_jd)
    nodal = [
        e for e in r.ledger if e.kind == "aspect" and e.statement.split()[0] in ("Rahu", "Ketu")
    ]
    assert nodal, "the reference chart should produce some nodal drishti"
    assert all(e.disputed for e in nodal)


def test_a_kind_that_cancels_itself_casts_no_vote(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    """Each kind votes once, on its own net, not once per evidence item."""
    r = _report(reference_chart, pinned_now_jd)
    for f in r.findings:
        counting = [e for e in f.evidence if not e.disputed]
        per_kind: dict[str, float] = {}
        for e in counting:
            per_kind[e.kind] = per_kind.get(e.kind, 0.0) + e.polarity * e.weight
        decisive = {k for k, v in per_kind.items() if abs(v) >= ev.KIND_DECISIVE}
        assert set(f.distinct_kinds) <= decisive


def test_every_evidence_item_is_sourced(reference_chart: ve.Chart, pinned_now_jd: float) -> None:
    r = _report(reference_chart, pinned_now_jd)
    assert r.ledger
    for e in r.ledger:
        assert e.source.strip(), f"{e.id} has no source"
        assert e.basis.strip(), f"{e.id} has no basis"
        assert e.kind in ev.FACTOR_KINDS
        assert e.polarity in (-1, 0, 1)


def test_evidence_ids_are_unique_and_resolvable(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    r = _report(reference_chart, pinned_now_jd)
    ids = [e.id for e in r.ledger]
    assert len(ids) == len(set(ids))
    known = set(ids)
    for f in r.findings:
        for cid in f.citations:
            assert cid in known


def test_verdicts_come_from_a_closed_set(
    reference_chart: ve.Chart, second_chart: ve.Chart, pinned_now_jd: float
) -> None:
    allowed = {
        "supported",
        "under strain",
        "contested (support and strain are each independently corroborated)",
    }
    for chart in (reference_chart, second_chart):
        for f in _report(chart, pinned_now_jd).findings:
            assert f.verdict in allowed


def test_gate_description_names_the_threshold(
    reference_chart: ve.Chart, pinned_now_jd: float
) -> None:
    gate = _report(reference_chart, pinned_now_jd).gate
    assert str(ev.MIN_DISTINCT_KINDS) in gate
    for kind in ev.FACTOR_KINDS:
        assert kind in gate
