"""
The evidence ledger and the multi-factor confirmation gate.

This is the part of the system that decides what may be said.

Practising astrologers who have tested language models on charts converge on
one rule: a reading is trustworthy only when a claim rests on several
independent chart factors, and an untrustworthy reading is one where the model
produced a fluent sentence from a single placement — or from nothing at all.
That rule is usually written into a prompt and then ignored, because a prompt
is a request, not a constraint.

Here it is a constraint. Every observation is recorded as a typed
:class:`Evidence` item naming the factor it came from and the text that
licenses it. A topic is reported only if at least
:data:`MIN_DISTINCT_KINDS` *different* kinds of factor support it. Anything
below the line is not softened or hedged — it is moved to a ``withheld`` list
with the reason, and the interpretation layer is told it may not discuss it.

The factor kinds are the ones the confirmation rule enumerates — house lord
placement, dignity, conjunction, aspect, nakshatra lord, yoga, dasha and
transit — plus ashtakavarga, which is a genuinely independent measure of house
strength and not reducible to the other eight.

Nothing in this module predicts. It reports which structural claims survive
the gate, and hands them on with their citations attached.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from . import ashtakavarga as av
from . import shadbala as sb
from .aspects import aspects_cast, conjunctions, house_lord, house_sign, nakshatra_chain, occupants
from .dignity import (
    DUSTHANAS,
    KENDRAS,
    TRIKONAS,
    UPACHAYAS,
    Dignity,
    all_dignities,
)
from .transits import transit_snapshot
from .vedic_engine import (
    Chart,
    current_periods,
    vimshottari_dasha,
)
from .yogas import YogaReport, detect_yogas

# The confirmation threshold. Two distinct kinds of factor, as the rule states.
MIN_DISTINCT_KINDS = 2

# How decisively one kind of factor must lean before it casts a vote. Item
# weights run from 1.0 to 1.6, so a lone item always clears this while a kind
# that roughly cancels itself out does not.
KIND_DECISIVE = 0.5

FACTOR_KINDS: tuple[str, ...] = (
    "house_lord_placement",
    "dignity",
    "conjunction",
    "aspect",
    "nakshatra_lord",
    "yoga",
    "dasha",
    "transit",
    "ashtakavarga",
)

HOUSE_TOPICS: dict[int, str] = {
    1: "self, body, and life direction",
    2: "wealth, speech, and family of origin",
    3: "courage, siblings, and initiative",
    4: "home, mother, and inner foundation",
    5: "children, creativity, and intelligence",
    6: "work, service, debt, and illness",
    7: "marriage and partnership",
    8: "crisis, inheritance, and hidden things",
    9: "fortune, father, dharma, and higher learning",
    10: "career, authority, and public standing",
    11: "gains, networks, and fulfilment of desire",
    12: "loss, foreign lands, retreat, and release",
}

CONFIDENCE_BANDS: dict[int, str] = {
    2: "indicative",
    3: "corroborated",
    4: "well corroborated",
}


@dataclass(frozen=True)
class Evidence:
    """One factual, sourced observation bearing on one topic."""

    id: str
    kind: str
    house: int
    statement: str
    basis: str
    source: str
    polarity: int  # +1 supportive, -1 obstructing, 0 neutral
    weight: float = 1.0
    disputed: bool = False

    @property
    def counts(self) -> bool:
        """Disputed material is displayed but never satisfies the gate."""
        return not self.disputed

    @property
    def line(self) -> str:
        mark = {1: "+", -1: "-", 0: "="}[self.polarity]
        return f"[{self.id}] {mark} {self.statement} ({self.basis}; {self.source})"


@dataclass(frozen=True)
class Finding:
    """A topic that cleared the gate."""

    house: int
    topic: str
    verdict: str
    confidence: str
    distinct_kinds: tuple[str, ...]
    evidence: tuple[Evidence, ...]
    net_polarity: float

    @property
    def statement(self) -> str:
        return (
            f"House {self.house} ({self.topic}) is {self.verdict}, on "
            f"{len(self.distinct_kinds)} independent kinds of factor "
            f"({', '.join(self.distinct_kinds)})."
        )

    @property
    def citations(self) -> tuple[str, ...]:
        return tuple(e.id for e in self.evidence)


@dataclass(frozen=True)
class Withheld:
    """A topic that did not clear the gate, and why."""

    house: int
    topic: str
    reason: str
    kinds_found: tuple[str, ...]
    evidence: tuple[Evidence, ...]


@dataclass
class EvidenceReport:
    findings: list[Finding] = field(default_factory=list)
    withheld: list[Withheld] = field(default_factory=list)
    ledger: list[Evidence] = field(default_factory=list)
    min_distinct_kinds: int = MIN_DISTINCT_KINDS

    @property
    def gate(self) -> str:
        return (
            f"A topic is reported only when at least {self.min_distinct_kinds} "
            f"distinct kinds of factor support it, drawn from: "
            f"{', '.join(FACTOR_KINDS)}. Disputed material never counts toward "
            f"the threshold."
        )

    def by_house(self, house: int) -> Finding | None:
        return next((f for f in self.findings if f.house == house), None)

    def evidence_for(self, house: int) -> list[Evidence]:
        return [e for e in self.ledger if e.house == house]


# ── evidence collection ───────────────────────────────────────────────


def _house_quality(house: int) -> tuple[int, str]:
    """Rough polarity contribution of a house placement, with the reason."""
    if house in TRIKONAS:
        return 1, "a trikona"
    if house in KENDRAS:
        return 1, "a kendra"
    if house in DUSTHANAS:
        return -1, "a dusthana"
    if house in UPACHAYAS:
        return 1, "an upachaya, which improves with time"
    return 0, "a neutral house"


def _dignity_polarity(d: Dignity) -> int:
    if d.score >= 1.0:
        return 1
    if d.score <= -0.75:
        return -1
    return 0


class _Ledger:
    """Accumulates evidence with stable, quotable ids."""

    def __init__(self) -> None:
        self.items: list[Evidence] = []
        self._counters: dict[int, int] = {}

    def add(
        self,
        *,
        kind: str,
        house: int,
        statement: str,
        basis: str,
        source: str,
        polarity: int,
        weight: float = 1.0,
        disputed: bool = False,
    ) -> Evidence:
        n = self._counters.get(house, 0) + 1
        self._counters[house] = n
        item = Evidence(
            id=f"H{house}-{n}",
            kind=kind,
            house=house,
            statement=statement,
            basis=basis,
            source=source,
            polarity=polarity,
            weight=weight,
            disputed=disputed,
        )
        self.items.append(item)
        return item


def _collect_house_lord(led: _Ledger, chart: Chart, dig: dict[str, Dignity], house: int) -> None:
    lord = house_lord(chart, house)
    p = chart.planets[lord]
    d = dig[lord]
    quality, why = _house_quality(p.house)
    polarity = quality if _dignity_polarity(d) == 0 else _dignity_polarity(d)
    led.add(
        kind="house_lord_placement",
        house=house,
        statement=(
            f"{lord}, lord of house {house}, sits in house {p.house} ({p.sign}), {d.state_phrase}"
        ),
        basis=(
            f"house {house} carries {house_sign(chart, house)}, ruled by {lord}; "
            f"house {p.house} is {why}; {d.state_reason}"
        ),
        source="Brihat Parashara Hora Shastra ch. 24 (bhava lordship)",
        polarity=polarity,
        weight=1.5,
    )


def _collect_occupants(
    led: _Ledger,
    chart: Chart,
    dig: dict[str, Dignity],
    strengths: dict[str, sb.Shadbala],
    house: int,
) -> None:
    for name in occupants(chart, house):
        d = dig[name]
        bits = [d.state_phrase]
        if d.combust:
            bits.append("combust")
        if d.retrograde:
            bits.append("retrograde")
        if d.dig_bala:
            bits.append("with directional strength")

        strength = strengths.get(name)
        strength_note = ""
        if strength is not None:
            strength_note = (
                f"; shadbala {strength.total_rupas} rupas against a requirement "
                f"of {strength.required_rupas} ({strength.verdict})"
            )

        polarity = _dignity_polarity(d)
        if polarity == 0:
            polarity = 1 if d.benefic else -1

        led.add(
            kind="dignity",
            house=house,
            statement=f"{name} occupies house {house}, {', '.join(bits)}",
            basis=f"{d.state_reason}; {d.benefic_reason}{strength_note}",
            source="Brihat Parashara Hora Shastra ch. 3 and ch. 27",
            polarity=polarity,
            weight=1.2,
        )


def _collect_conjunctions(led: _Ledger, chart: Chart, dig: dict[str, Dignity], house: int) -> None:
    for c in conjunctions(chart):
        if c.house != house:
            continue
        benefics = [p for p in c.planets if dig[p].benefic]
        malefics = [p for p in c.planets if not dig[p].benefic]
        polarity = 1 if len(benefics) > len(malefics) else (-1 if malefics else 0)
        led.add(
            kind="conjunction",
            house=house,
            statement=f"{' and '.join(c.planets)} are conjunct in house {house}",
            basis=(
                f"all share {c.sign}, spread {c.max_separation}°"
                f"{', a tight yuti' if c.close else ''}; "
                f"{len(benefics)} benefic and {len(malefics)} malefic"
            ),
            source="Brihat Parashara Hora Shastra ch. 4 (yuti)",
            polarity=polarity,
            weight=1.2,
        )


def _collect_aspects(led: _Ledger, chart: Chart, dig: dict[str, Dignity], house: int) -> None:
    for asp in aspects_cast(chart):
        if asp.target_house != house:
            continue
        d = dig[asp.source]
        led.add(
            kind="aspect",
            house=house,
            statement=f"{asp.source} casts drishti on house {house}",
            basis=f"{asp.rule}; {asp.source} is {d.state_phrase} and functionally {d.functional}",
            source="Brihat Parashara Hora Shastra ch. 26",
            polarity=1 if d.benefic else -1,
            weight=1.0,
            disputed=asp.disputed,
        )


def _collect_nakshatra_lord(led: _Ledger, chart: Chart, house: int) -> None:
    lord = house_lord(chart, house)
    chain = nakshatra_chain(chart, lord)
    star = chart.planets[lord].nak_lord
    star_p = chart.planets[star]
    quality, why = _house_quality(star_p.house)
    led.add(
        kind="nakshatra_lord",
        house=house,
        statement=(
            f"{lord}, lord of house {house}, sits in {chart.planets[lord].nakshatra}, "
            f"whose lord {star} occupies house {star_p.house}"
        ),
        basis=(f"chain {' -> '.join(chain.path)}; {chain.note}; house {star_p.house} is {why}"),
        source="Bhrigu Nandi Nadi chain method; Krishnamurti Paddhati star lord rule",
        polarity=quality,
        weight=1.0,
    )


def _collect_yogas(led: _Ledger, yreport: YogaReport, house: int) -> None:
    for y in yreport.formed:
        if house not in y.houses:
            continue
        led.add(
            kind="yoga",
            house=house,
            statement=f"{y.name} involves house {house}",
            basis=f"{y.detail}; rule: {y.rule}",
            source=y.source,
            polarity=y.polarity,
            weight=1.6,
            disputed=y.disputed,
        )


def _collect_dasha(
    led: _Ledger,
    chart: Chart,
    house: int,
    maha: tuple | None,
    antar: tuple | None,
) -> None:
    lord = house_lord(chart, house)
    for period, label in ((maha, "mahadasha"), (antar, "antardasha")):
        if not period:
            continue
        plord = period[0]
        reasons: list[str] = []
        if plord == lord:
            reasons.append(f"the running {label} lord {plord} rules house {house}")
        if chart.planets[plord].house == house:
            reasons.append(f"the running {label} lord {plord} occupies house {house}")
        if not reasons:
            continue
        led.add(
            kind="dasha",
            house=house,
            statement=f"House {house} is activated by the running {label}",
            basis="; ".join(reasons),
            source="Vimshottari dasha, anchored to the natal Moon's nakshatra",
            polarity=0,
            weight=1.5,
        )


def _collect_transits(led: _Ledger, chart: Chart, house: int, snapshot: dict) -> None:
    for planet, pos in snapshot.items():
        if pos.house_from_lagna != house:
            continue
        note = f"; {pos.condition}" if pos.condition else ""
        led.add(
            kind="transit",
            house=house,
            statement=f"{planet} is currently transiting house {house}",
            basis=(
                f"{planet} in {pos.sign} at {pos.degree:.2f}°, the "
                f"{pos.house_from_moon} from the natal Moon"
                f"{', retrograde' if pos.retrograde else ''}{note}"
            ),
            source="Gochara from the natal lagna and Moon (Phaladeepika ch. 26)",
            polarity=-1 if planet in ("Saturn", "Rahu", "Ketu") else 1,
            weight=1.0,
        )


def _collect_ashtakavarga(led: _Ledger, report: av.AshtakavargaReport, house: int) -> None:
    points = report.sarva_in_house(house)
    if points >= av.SAV_RICH:
        polarity, band = 1, "well supplied"
    elif points <= av.SAV_POOR:
        polarity, band = -1, "thinly supplied"
    else:
        polarity, band = 0, "average"
    led.add(
        kind="ashtakavarga",
        house=house,
        statement=f"House {house} carries {points} sarvashtakavarga points ({band})",
        basis=(
            f"{points} of a 337-point total; {av.SAV_RICH}+ counts as strong and "
            f"{av.SAV_POOR} or fewer as weak"
        ),
        source="Brihat Parashara Hora Shastra ch. 66-70",
        polarity=polarity,
        weight=1.0,
    )


# ── the gate ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GateOutcome:
    """The verdict of the confirmation rule on one group of evidence."""

    passed: bool
    verdict: str
    kinds: tuple[str, ...]
    depth: int
    net: float
    supporting_kinds: tuple[str, ...]
    opposing_kinds: tuple[str, ...]

    @property
    def confidence(self) -> str:
        return CONFIDENCE_BANDS.get(self.depth, "strongly corroborated")

    def failure_reason(self, subject: str) -> str:
        return (
            f"no direction reached the threshold: {len(self.supporting_kinds)} "
            f"kind(s) of factor support this and {len(self.opposing_kinds)} "
            f"oppose it, against a requirement of {MIN_DISTINCT_KINDS} agreeing "
            f"kinds. Nothing about {subject} is supportable from this evidence."
        )


def run_gate(items: Sequence[Evidence]) -> GateOutcome:
    """Apply the confirmation rule to one group of evidence.

    Two decisions make this rule mean something, and both were bugs before
    they were features:

    First, the threshold is applied *per direction*, not to the pile as a
    whole. Every house always has a lord somewhere, a nakshatra chain and an
    ashtakavarga score, so counting mere presence passed all twelve houses on
    every chart. What has to clear the bar is agreement — two distinct kinds
    of factor pointing the same way. Neutral observations are context, not
    support.

    Second, each kind is resolved to its own net before it votes. Every house
    receives both benefic and malefic drishti, so treating each aspect as its
    own vote let "aspect" support both directions at once and everything came
    back contested. A kind that cancels itself out is not evidence for
    anything.

    This function is the single source of truth for the rule; the natal and
    compatibility layers both route through it.
    """
    counting = [e for e in items if e.counts]

    per_kind: dict[str, float] = {}
    for e in counting:
        per_kind[e.kind] = per_kind.get(e.kind, 0.0) + e.polarity * e.weight

    s_kinds = tuple(k for k, v in per_kind.items() if v >= KIND_DECISIVE)
    o_kinds = tuple(k for k, v in per_kind.items() if v <= -KIND_DECISIVE)
    s_ok = len(s_kinds) >= MIN_DISTINCT_KINDS
    o_ok = len(o_kinds) >= MIN_DISTINCT_KINDS
    net = sum(e.polarity * e.weight for e in counting)

    if not s_ok and not o_ok:
        return GateOutcome(
            passed=False,
            verdict="withheld",
            kinds=tuple(dict.fromkeys(e.kind for e in counting)),
            depth=0,
            net=round(net, 2),
            supporting_kinds=s_kinds,
            opposing_kinds=o_kinds,
        )

    if s_ok and o_ok:
        verdict = "contested (support and strain are each independently corroborated)"
        kinds = tuple(dict.fromkeys(s_kinds + o_kinds))
        depth = max(len(s_kinds), len(o_kinds))
    elif s_ok:
        verdict, kinds, depth = "supported", s_kinds, len(s_kinds)
    else:
        verdict, kinds, depth = "under strain", o_kinds, len(o_kinds)

    return GateOutcome(
        passed=True,
        verdict=verdict,
        kinds=kinds,
        depth=depth,
        net=round(net, 2),
        supporting_kinds=s_kinds,
        opposing_kinds=o_kinds,
    )


def build_evidence(chart: Chart, birth_jd: float, now_jd: float) -> EvidenceReport:
    """Collect every factor, then let only what clears the gate through."""
    dig = all_dignities(chart)
    strengths = sb.all_shadbala(chart)
    yreport = detect_yogas(chart)
    avreport = av.compute_ashtakavarga(chart)
    snapshot = transit_snapshot(chart, now_jd)
    dashas = vimshottari_dasha(chart.planets["Moon"].longitude, birth_jd)
    maha, antar, _ = current_periods(dashas, now_jd)

    led = _Ledger()
    for house in range(1, 13):
        _collect_house_lord(led, chart, dig, house)
        _collect_occupants(led, chart, dig, strengths, house)
        _collect_conjunctions(led, chart, dig, house)
        _collect_aspects(led, chart, dig, house)
        _collect_nakshatra_lord(led, chart, house)
        _collect_yogas(led, yreport, house)
        _collect_dasha(led, chart, house, maha, antar)
        _collect_transits(led, chart, house, snapshot)
        _collect_ashtakavarga(led, avreport, house)

    report = EvidenceReport(ledger=led.items)

    for house in range(1, 13):
        items = tuple(e for e in led.items if e.house == house)
        outcome = run_gate(items)

        if not outcome.passed:
            report.withheld.append(
                Withheld(
                    house=house,
                    topic=HOUSE_TOPICS[house],
                    reason=outcome.failure_reason(f"house {house} ({HOUSE_TOPICS[house]})"),
                    kinds_found=outcome.kinds,
                    evidence=items,
                )
            )
            continue

        report.findings.append(
            Finding(
                house=house,
                topic=HOUSE_TOPICS[house],
                verdict=outcome.verdict,
                confidence=outcome.confidence,
                distinct_kinds=outcome.kinds,
                evidence=items,
                net_polarity=outcome.net,
            )
        )

    return report
