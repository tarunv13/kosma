"""
Aspects, conjunctions, and lordship chains.

Purely mechanical geometry over a computed chart. Each result carries the rule
that produced it so the evidence layer can quote a source rather than assert a
relationship from memory.

Sources
-------
* Brihat Parashara Hora Shastra ch. 26 — graha drishti, including the special
  aspects of Mars, Jupiter and Saturn.
* Jaimini Sutras 1.1 — rashi drishti (sign-to-sign aspect by modality).
* Bhrigu Nandi Nadi practice — planetary chains built through sign lords and
  nakshatra lords.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dignity import SIGN_LORDS
from .vedic_engine import SIGNS, VEDIC_PLANETS, Chart

# ── Graha drishti (BPHS ch. 26) ───────────────────────────────────────
# Every graha aspects the 7th from itself with full strength. Mars, Jupiter
# and Saturn have additional full special aspects.

SPECIAL_ASPECTS: dict[str, tuple[int, ...]] = {
    "Mars": (4, 8),
    "Jupiter": (5, 9),
    "Saturn": (3, 10),
}

# Nodal aspects are not in BPHS. Many later schools grant Rahu and Ketu the
# 5th, 7th and 9th. Emitted, but flagged so the confirmation gate can discount
# them.
NODAL_ASPECTS: tuple[int, ...] = (5, 7, 9)

MODALITY = ("movable", "fixed", "dual")


@dataclass(frozen=True)
class Aspect:
    """One planet casting drishti onto one house."""

    source: str
    target_house: int
    target_sign: str
    distance: int  # nth house from the source, 1-indexed
    rule: str
    disputed: bool = False

    @property
    def label(self) -> str:
        return f"{self.source} aspects H{self.target_house} ({self.target_sign})"


def aspects_cast(chart: Chart) -> list[Aspect]:
    """Every graha drishti in the chart, source-ordered."""
    out: list[Aspect] = []
    asc = chart.ascendant_sign_idx
    for name in VEDIC_PLANETS:
        p = chart.planets[name]
        if name in ("Rahu", "Ketu"):
            distances = NODAL_ASPECTS
            disputed = True
            rule_base = "not given aspects in BPHS; the 5th/7th/9th are assigned by later schools"
        else:
            distances = (7, *SPECIAL_ASPECTS.get(name, ()))
            disputed = False
            rule_base = "BPHS ch. 26"

        for dist in sorted(distances):
            target_sign_idx = (p.sign_idx + dist - 1) % 12
            house = ((target_sign_idx - asc) % 12) + 1
            if dist == 7:
                rule = f"every graha aspects the 7th from itself ({rule_base})"
            else:
                rule = f"{name} has a special full aspect on the {_ord(dist)} ({rule_base})"
            out.append(
                Aspect(
                    source=name,
                    target_house=house,
                    target_sign=SIGNS[target_sign_idx],
                    distance=dist,
                    rule=rule,
                    disputed=disputed,
                )
            )
    return out


def aspects_on_house(chart: Chart, house: int) -> list[Aspect]:
    """Every aspect landing on ``house``."""
    return [a for a in aspects_cast(chart) if a.target_house == house]


def aspects_on_planet(chart: Chart, planet: str) -> list[Aspect]:
    """Every aspect landing on the sign occupied by ``planet``."""
    target = chart.planets[planet].house
    return [a for a in aspects_cast(chart) if a.target_house == target and a.source != planet]


def mutual_aspects(chart: Chart) -> list[tuple[str, str, str]]:
    """Pairs of planets that aspect each other, with the governing rule."""
    landing: dict[int, set[str]] = {}
    for asp in aspects_cast(chart):
        landing.setdefault(asp.target_house, set()).add(asp.source)

    out: list[tuple[str, str, str]] = []
    for i, a in enumerate(VEDIC_PLANETS):
        for b in VEDIC_PLANETS[i + 1 :]:
            ha = chart.planets[a].house
            hb = chart.planets[b].house
            if a in landing.get(hb, set()) and b in landing.get(ha, set()):
                out.append((a, b, "mutual full aspect (BPHS ch. 26)"))
    return out


# ── Rashi drishti (Jaimini Sutras 1.1) ────────────────────────────────


def rashi_drishti(sign_idx: int) -> list[int]:
    """Sign-to-sign aspect by modality.

    A movable sign aspects the fixed signs other than the one adjacent to it;
    a fixed sign aspects the movable signs other than the one adjacent to it;
    a dual sign aspects the other three dual signs.
    """
    modality = sign_idx % 3
    if modality == 0:  # movable
        return [i for i in range(12) if i % 3 == 1 and i != (sign_idx + 1) % 12]
    if modality == 1:  # fixed
        return [i for i in range(12) if i % 3 == 0 and i != (sign_idx - 1) % 12]
    return [i for i in range(12) if i % 3 == 2 and i != sign_idx]  # dual


# ── Conjunctions ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class Conjunction:
    """Two or more grahas sharing one sign."""

    planets: tuple[str, ...]
    sign: str
    house: int
    max_separation: float
    close: bool  # within 5 degrees — a tight yuti

    @property
    def label(self) -> str:
        joined = " + ".join(self.planets)
        tight = f", tight ({self.max_separation:.1f}°)" if self.close else ""
        return f"{joined} conjunct in {self.sign} (H{self.house}){tight}"


def conjunctions(chart: Chart) -> list[Conjunction]:
    """All same-sign conjunctions, ordered by house."""
    by_sign: dict[int, list[str]] = {}
    for name in VEDIC_PLANETS:
        by_sign.setdefault(chart.planets[name].sign_idx, []).append(name)

    out: list[Conjunction] = []
    for sign_idx, names in sorted(by_sign.items()):
        if len(names) < 2:
            continue
        degs = [chart.planets[n].deg_in_sign for n in names]
        spread = max(degs) - min(degs)
        out.append(
            Conjunction(
                planets=tuple(names),
                sign=SIGNS[sign_idx],
                house=chart.planets[names[0]].house,
                max_separation=round(spread, 3),
                close=spread <= 5.0,
            )
        )
    return sorted(out, key=lambda c: c.house)


# ── Lordship and nakshatra chains (Bhrigu Nandi Nadi step) ────────────


@dataclass(frozen=True)
class Chain:
    """A dispositor or nakshatra-lord chain and where it settles."""

    planet: str
    kind: str  # "dispositor" | "nakshatra"
    path: tuple[str, ...]
    terminus: str
    note: str


def dispositor_chain(chart: Chart, planet: str) -> Chain:
    """Follow sign lords from ``planet`` until the chain repeats."""
    path: list[str] = [planet]
    seen = {planet}
    current = planet
    while True:
        lord = SIGN_LORDS[chart.planets[current].sign]
        if lord == current:
            return Chain(
                planet=planet,
                kind="dispositor",
                path=tuple(path),
                terminus=current,
                note=f"{current} sits in its own sign, so the chain ends there",
            )
        if lord in seen:
            loop = path[path.index(lord) :]
            return Chain(
                planet=planet,
                kind="dispositor",
                path=tuple(path),
                terminus=lord,
                note=f"the chain closes into a loop: {' -> '.join(loop)} -> {lord}",
            )
        path.append(lord)
        seen.add(lord)
        current = lord


def nakshatra_chain(chart: Chart, planet: str) -> Chain:
    """Follow nakshatra lords from ``planet`` until the chain repeats."""
    path: list[str] = [planet]
    seen = {planet}
    current = planet
    while True:
        lord = chart.planets[current].nak_lord
        if lord == current:
            return Chain(
                planet=planet,
                kind="nakshatra",
                path=tuple(path),
                terminus=current,
                note=f"{current} occupies its own nakshatra, so the chain ends there",
            )
        if lord in seen:
            loop = path[path.index(lord) :]
            return Chain(
                planet=planet,
                kind="nakshatra",
                path=tuple(path),
                terminus=lord,
                note=f"the chain closes into a loop: {' -> '.join(loop)} -> {lord}",
            )
        path.append(lord)
        seen.add(lord)
        current = lord


def all_chains(chart: Chart) -> dict[str, dict[str, Chain]]:
    """Both chain kinds for every graha."""
    return {
        name: {
            "dispositor": dispositor_chain(chart, name),
            "nakshatra": nakshatra_chain(chart, name),
        }
        for name in VEDIC_PLANETS
    }


# ── House occupancy ───────────────────────────────────────────────────


def occupants(chart: Chart, house: int) -> list[str]:
    """Grahas sitting in ``house``."""
    return [n for n in VEDIC_PLANETS if chart.planets[n].house == house]


def house_lord(chart: Chart, house: int) -> str:
    """Ruler of the sign on ``house`` counted whole-sign from the lagna."""
    sign_idx = (chart.ascendant_sign_idx + house - 1) % 12
    return SIGN_LORDS[SIGNS[sign_idx]]


def house_sign(chart: Chart, house: int) -> str:
    return SIGNS[(chart.ascendant_sign_idx + house - 1) % 12]


def _ord(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"
