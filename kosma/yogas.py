"""
Yoga detection from an explicit, sourced rule table.

The rule for this module is the one the practising astrologers in the field
keep repeating about AI: *do not invent yogas*. So every yoga here is detected
by a written condition, reports the planets and houses that formed it, and
names the text it comes from. A yoga that is not formed is simply absent — the
module never reaches for something that "feels right".

Where a widely-quoted yoga has no classical basis (Kala Sarpa is the usual
example) it is emitted with ``disputed=True`` and the absence is stated
plainly, so the confirmation gate can refuse to count it.

Sources
-------
* Brihat Parashara Hora Shastra ch. 34-41 — raja, dhana, and nabhasa yogas.
* Phaladeepika ch. 6-7 — vipreeta raja yoga, parivartana, adhi yoga.
* Saravali ch. 34-38 — pancha mahapurusha, lunar yogas.
* Jataka Parijata ch. 7 — neechabhanga conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .aspects import aspects_cast, house_lord, house_sign, occupants
from .dignity import EXALTATION, MOOLATRIKONA, OWN_SIGNS, SIGN_LORDS
from .vedic_engine import SIGNS, VEDIC_PLANETS, Chart

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
DUSTHANA_HOUSES = (6, 8, 12)
DHANA_HOUSES = (1, 2, 5, 9, 11)

TRUE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
BENEFICS = ("Jupiter", "Venus", "Mercury")

MAHAPURUSHA_NAMES: dict[str, str] = {
    "Mars": "Ruchaka",
    "Mercury": "Bhadra",
    "Jupiter": "Hamsa",
    "Venus": "Malavya",
    "Saturn": "Sasa",
}

# sign -> the planet exalted in it, for neechabhanga condition (b)
_EXALTED_IN: dict[str, str] = {sign: planet for planet, (sign, _) in EXALTATION.items()}


@dataclass(frozen=True)
class Yoga:
    """One formed yoga, with the rule and text that justify it."""

    name: str
    rule: str
    source: str
    planets: tuple[str, ...]
    houses: tuple[int, ...]
    detail: str
    polarity: int  # +1 auspicious, -1 inauspicious, 0 mixed
    caveat: str | None = None
    disputed: bool = False

    @property
    def label(self) -> str:
        return f"{self.name}: {self.detail}"


# ── shared helpers ────────────────────────────────────────────────────


def _aspect_pairs(chart: Chart) -> set[tuple[str, str]]:
    """``(a, b)`` when ``a`` casts drishti onto the sign holding ``b``."""
    houses = {n: chart.planets[n].house for n in VEDIC_PLANETS}
    pairs: set[tuple[str, str]] = set()
    for asp in aspects_cast(chart):
        if asp.disputed:
            continue  # nodal aspects are not used to form yogas
        for target, house in houses.items():
            if house == asp.target_house and target != asp.source:
                pairs.add((asp.source, target))
    return pairs


def _same_sign(chart: Chart, a: str, b: str) -> bool:
    return chart.planets[a].sign_idx == chart.planets[b].sign_idx


def _exchange(chart: Chart, a: str, b: str) -> bool:
    """``a`` sits in a sign owned by ``b`` and vice versa."""
    return chart.planets[a].sign in OWN_SIGNS.get(b, []) and chart.planets[b].sign in OWN_SIGNS.get(
        a, []
    )


def _relation(chart: Chart, a: str, b: str, pairs: set[tuple[str, str]]) -> str | None:
    """The sambandha (connection) between two planets, if any."""
    if a == b:
        return None
    if _same_sign(chart, a, b):
        return "conjunction"
    if _exchange(chart, a, b):
        return "mutual exchange of signs"
    if (a, b) in pairs and (b, a) in pairs:
        return "mutual aspect"
    return None


def _house_from_moon(chart: Chart, planet: str) -> int:
    moon_idx = chart.planets["Moon"].sign_idx
    return ((chart.planets[planet].sign_idx - moon_idx) % 12) + 1


def _sign_house_from_moon(chart: Chart, sign_idx: int) -> int:
    moon_idx = chart.planets["Moon"].sign_idx
    return ((sign_idx - moon_idx) % 12) + 1


# ── individual detectors ──────────────────────────────────────────────


def _raja_yogas(chart: Chart, pairs: set[tuple[str, str]]) -> list[Yoga]:
    out: list[Yoga] = []
    kendra_lords = {house_lord(chart, h): h for h in KENDRA_HOUSES}
    trikona_lords = {house_lord(chart, h): h for h in TRIKONA_HOUSES}

    seen: set[frozenset[str]] = set()
    for kl, kh in kendra_lords.items():
        for tl, th in trikona_lords.items():
            if kl == tl:
                continue
            key = frozenset((kl, tl))
            if key in seen:
                continue
            rel = _relation(chart, kl, tl, pairs)
            if not rel:
                continue
            seen.add(key)
            out.append(
                Yoga(
                    name="Raja Yoga",
                    rule=(
                        "A lord of a kendra (1, 4, 7, 10) and a lord of a trikona "
                        "(1, 5, 9) joined by conjunction, mutual aspect, or exchange."
                    ),
                    source="Brihat Parashara Hora Shastra ch. 41",
                    planets=(kl, tl),
                    houses=(kh, th),
                    detail=(
                        f"{kl}, lord of the {_ord(kh)}, and {tl}, lord of the "
                        f"{_ord(th)}, are in {rel}"
                    ),
                    polarity=1,
                )
            )

    # A single planet ruling both a kendra and a trikona is itself a yogakaraka.
    for planet in TRUE_PLANETS:
        ruled = sorted(
            ((SIGNS.index(s) - chart.ascendant_sign_idx) % 12) + 1
            for s in OWN_SIGNS.get(planet, [])
        )
        k = [h for h in ruled if h in (4, 7, 10)]
        # The 5th and 9th only: the lagna is both a kendra and a trikona, so
        # counting it would make a yogakaraka of every lagna lord holding a
        # kendra. Excluding it reproduces the classical set exactly.
        t = [h for h in ruled if h in (5, 9)]
        if k and t:
            out.append(
                Yoga(
                    name="Yogakaraka",
                    rule=(
                        "A single planet owning both a kendra and a trikona from the "
                        "lagna acts as a raja yoga in its own right."
                    ),
                    source="Brihat Parashara Hora Shastra ch. 34",
                    planets=(planet,),
                    houses=tuple(sorted(k + t)),
                    detail=(
                        f"{planet} rules the {_ord(k[0])} (kendra) and the {_ord(t[0])} (trikona)"
                    ),
                    polarity=1,
                )
            )
    return out


def _dhana_yogas(chart: Chart, pairs: set[tuple[str, str]]) -> list[Yoga]:
    out: list[Yoga] = []
    lords = {h: house_lord(chart, h) for h in DHANA_HOUSES}
    seen: set[frozenset[str]] = set()
    houses = sorted(DHANA_HOUSES)
    for i, h1 in enumerate(houses):
        for h2 in houses[i + 1 :]:
            a, b = lords[h1], lords[h2]
            if a == b:
                continue
            key = frozenset((a, b))
            if key in seen:
                continue
            rel = _relation(chart, a, b, pairs)
            if not rel:
                continue
            seen.add(key)
            out.append(
                Yoga(
                    name="Dhana Yoga",
                    rule=(
                        "Lords of the wealth-giving houses (1, 2, 5, 9, 11) connected "
                        "by conjunction, mutual aspect, or exchange."
                    ),
                    source="Phaladeepika ch. 6",
                    planets=(a, b),
                    houses=(h1, h2),
                    detail=(
                        f"{a}, lord of the {_ord(h1)}, and {b}, lord of the "
                        f"{_ord(h2)}, are in {rel}"
                    ),
                    polarity=1,
                )
            )
    return out


def _vipreeta_yogas(chart: Chart) -> list[Yoga]:
    names = {6: "Harsha", 8: "Sarala", 12: "Vimala"}
    out: list[Yoga] = []
    for h, label in names.items():
        lord = house_lord(chart, h)
        lord_house = chart.planets[lord].house
        if lord_house in DUSTHANA_HOUSES:
            out.append(
                Yoga(
                    name=f"Vipreeta Raja Yoga ({label})",
                    rule=(
                        f"The lord of the {_ord(h)} placed in a dusthana "
                        "(6th, 8th or 12th) — one difficulty undoing another."
                    ),
                    source="Phaladeepika ch. 6",
                    planets=(lord,),
                    houses=(h, lord_house),
                    detail=f"{lord}, lord of the {_ord(h)}, sits in the {_ord(lord_house)}",
                    polarity=1,
                    caveat=(
                        "Vipreeta yogas classically deliver through disruption rather "
                        "than ease, and authors differ on whether the lord may sit in "
                        "its own dusthana."
                    ),
                )
            )
    return out


def _neechabhanga(chart: Chart, pairs: set[tuple[str, str]]) -> list[Yoga]:
    out: list[Yoga] = []
    for planet in TRUE_PLANETS:
        exalt = EXALTATION.get(planet)
        if not exalt:
            continue
        deb_sign = SIGNS[(SIGNS.index(exalt[0]) + 6) % 12]
        p = chart.planets[planet]
        if p.sign != deb_sign:
            continue

        dispositor = SIGN_LORDS[deb_sign]
        exalted_here = _EXALTED_IN.get(deb_sign)
        conditions: list[str] = []

        if chart.planets[dispositor].house in KENDRA_HOUSES:
            conditions.append(
                f"the dispositor {dispositor} occupies a kendra from the lagna "
                f"(the {_ord(chart.planets[dispositor].house)})"
            )
        if _house_from_moon(chart, dispositor) in KENDRA_HOUSES:
            conditions.append(
                f"the dispositor {dispositor} occupies a kendra from the Moon "
                f"(the {_ord(_house_from_moon(chart, dispositor))})"
            )
        if exalted_here and chart.planets[exalted_here].house in KENDRA_HOUSES:
            conditions.append(
                f"{exalted_here}, which is exalted in {deb_sign}, occupies a kendra "
                f"from the lagna (the {_ord(chart.planets[exalted_here].house)})"
            )
        if _same_sign(chart, planet, dispositor):
            conditions.append(f"{planet} is conjunct its dispositor {dispositor}")
        elif (dispositor, planet) in pairs:
            conditions.append(f"{planet} is aspected by its dispositor {dispositor}")
        if p.house in KENDRA_HOUSES:
            conditions.append(
                f"the debilitated {planet} itself occupies a kendra from the lagna "
                f"(the {_ord(p.house)})"
            )

        if not conditions:
            continue
        out.append(
            Yoga(
                name="Neechabhanga Raja Yoga",
                rule=(
                    "A debilitated planet whose debility is cancelled — by its "
                    "dispositor or the sign's exaltation lord standing in a kendra "
                    "from the lagna or Moon, by conjunction or aspect from the "
                    "dispositor, or by the planet itself holding a kendra."
                ),
                source="Jataka Parijata ch. 7; Brihat Parashara Hora Shastra ch. 34",
                planets=(planet, dispositor),
                houses=(p.house,),
                detail=(
                    f"{planet} is debilitated in {deb_sign} (H{p.house}); "
                    f"cancellation holds because {_and_join(conditions)}"
                ),
                polarity=1,
                caveat=(
                    "Authors differ on how completely neechabhanga restores a planet; "
                    "many hold that results arrive only after struggle."
                ),
            )
        )
    return out


def _parivartana(chart: Chart) -> list[Yoga]:
    out: list[Yoga] = []
    seen: set[frozenset[str]] = set()
    for h1 in range(1, 13):
        for h2 in range(h1 + 1, 13):
            a, b = house_lord(chart, h1), house_lord(chart, h2)
            if a == b or frozenset((a, b)) in seen:
                continue
            if not _exchange(chart, a, b):
                continue
            seen.add(frozenset((a, b)))

            if h1 in DUSTHANA_HOUSES or h2 in DUSTHANA_HOUSES:
                kind, polarity = "Dainya", -1
                gloss = "an exchange touching a dusthana, which classically drains it"
            elif 3 in (h1, h2):
                kind, polarity = "Khala", 0
                gloss = "an exchange involving the 3rd, giving mixed and uneven results"
            else:
                kind, polarity = "Maha", 1
                gloss = "an exchange between two auspicious houses"

            out.append(
                Yoga(
                    name=f"Parivartana Yoga ({kind})",
                    rule=(
                        "Two house lords occupying each other's signs. Phaladeepika "
                        "grades the exchange Maha, Dainya, or Khala by the houses "
                        "involved."
                    ),
                    source="Phaladeepika ch. 6",
                    planets=(a, b),
                    houses=(h1, h2),
                    detail=(
                        f"{a} (lord of the {_ord(h1)}) and {b} (lord of the "
                        f"{_ord(h2)}) occupy each other's signs — {gloss}"
                    ),
                    polarity=polarity,
                )
            )
    return out


def _mahapurusha(chart: Chart) -> list[Yoga]:
    out: list[Yoga] = []
    for planet, label in MAHAPURUSHA_NAMES.items():
        p = chart.planets[planet]
        if p.house not in KENDRA_HOUSES:
            continue
        exalt = EXALTATION.get(planet)
        mt = MOOLATRIKONA.get(planet)
        if exalt and p.sign == exalt[0]:
            dignity = "exalted"
        elif mt and p.sign == mt[0] and mt[1] <= p.deg_in_sign < mt[2]:
            dignity = "in moolatrikona"
        elif p.sign in OWN_SIGNS.get(planet, []):
            dignity = "in its own sign"
        else:
            continue
        out.append(
            Yoga(
                name=f"{label} Yoga (Pancha Mahapurusha)",
                rule=(
                    "Mars, Mercury, Jupiter, Venus or Saturn standing in its own "
                    "sign, moolatrikona, or exaltation while occupying a kendra "
                    "from the lagna."
                ),
                source="Saravali ch. 38",
                planets=(planet,),
                houses=(p.house,),
                detail=f"{planet} is {dignity} in {p.sign} and holds the {_ord(p.house)}",
                polarity=1,
            )
        )
    return out


def _lunar_yogas(chart: Chart, pairs: set[tuple[str, str]]) -> list[Yoga]:
    out: list[Yoga] = []
    moon_idx = chart.planets["Moon"].sign_idx

    # Gajakesari — Jupiter in a kendra from the Moon.
    jup_from_moon = _house_from_moon(chart, "Jupiter")
    if jup_from_moon in KENDRA_HOUSES:
        out.append(
            Yoga(
                name="Gajakesari Yoga",
                rule="Jupiter occupying a kendra (1, 4, 7, 10) counted from the Moon.",
                source="Phaladeepika ch. 6",
                planets=("Jupiter", "Moon"),
                houses=(chart.planets["Jupiter"].house,),
                detail=f"Jupiter stands in the {_ord(jup_from_moon)} from the Moon",
                polarity=1,
            )
        )

    # Sunapha / Anapha / Durudhara — company around the Moon, Sun and nodes excluded.
    def _tenants(offset: int) -> list[str]:
        target = (moon_idx + offset) % 12
        return [
            n
            for n in TRUE_PLANETS
            if n not in ("Sun", "Moon") and chart.planets[n].sign_idx == target
        ]

    second = _tenants(1)
    twelfth = _tenants(-1)
    if second and twelfth:
        out.append(
            Yoga(
                name="Durudhara Yoga",
                rule=(
                    "Planets other than the Sun and the nodes occupying both the 2nd "
                    "and the 12th from the Moon."
                ),
                source="Saravali ch. 34",
                planets=tuple(second + twelfth),
                houses=(chart.planets["Moon"].house,),
                detail=(
                    f"{_and_join(second)} {_agree(second, 'sits', 'sit')} in the 2nd "
                    f"from the Moon and {_and_join(twelfth)} in the 12th"
                ),
                polarity=1,
            )
        )
    elif second:
        out.append(
            Yoga(
                name="Sunapha Yoga",
                rule=("Planets other than the Sun and the nodes occupying the 2nd from the Moon."),
                source="Saravali ch. 34",
                planets=tuple(second),
                houses=(chart.planets["Moon"].house,),
                detail=(
                    f"{_and_join(second)} {_agree(second, 'occupies', 'occupy')} "
                    "the 2nd from the Moon"
                ),
                polarity=1,
            )
        )
    elif twelfth:
        out.append(
            Yoga(
                name="Anapha Yoga",
                rule=("Planets other than the Sun and the nodes occupying the 12th from the Moon."),
                source="Saravali ch. 34",
                planets=tuple(twelfth),
                houses=(chart.planets["Moon"].house,),
                detail=(
                    f"{_and_join(twelfth)} {_agree(twelfth, 'occupies', 'occupy')} "
                    "the 12th from the Moon"
                ),
                polarity=1,
            )
        )
    else:
        with_moon = [
            n
            for n in TRUE_PLANETS
            if n not in ("Sun", "Moon") and chart.planets[n].sign_idx == moon_idx
        ]
        if not with_moon:
            cancels: list[str] = []
            if chart.planets["Moon"].house in KENDRA_HOUSES:
                cancels.append(
                    f"the Moon itself holds a kendra from the lagna "
                    f"(the {_ord(chart.planets['Moon'].house)})"
                )
            aspecting = [b for (a, b) in [(x, y) for (x, y) in pairs if y == "Moon"] for b in [a]]
            benefic_aspects = [a for a in aspecting if a in BENEFICS]
            if benefic_aspects:
                cancels.append(f"the Moon receives aspect from {_and_join(benefic_aspects)}")
            out.append(
                Yoga(
                    name="Kemadruma Yoga",
                    rule=(
                        "No planet other than the Sun and the nodes in the 2nd, the "
                        "12th, or the same sign as the Moon."
                    ),
                    source="Saravali ch. 34",
                    planets=("Moon",),
                    houses=(chart.planets["Moon"].house,),
                    detail="the Moon stands without company in the 2nd, 12th, or its own sign",
                    polarity=-1,
                    caveat=(
                        "Cancellation applies: " + _and_join(cancels) + "."
                        if cancels
                        else "No classical cancellation condition was found in this chart."
                    ),
                )
            )

    # Chandra-Mangala — Moon and Mars connected.
    rel = _relation(chart, "Moon", "Mars", pairs)
    if rel:
        out.append(
            Yoga(
                name="Chandra-Mangala Yoga",
                rule="The Moon and Mars joined by conjunction, mutual aspect, or exchange.",
                source="Brihat Parashara Hora Shastra ch. 36",
                planets=("Moon", "Mars"),
                houses=(chart.planets["Moon"].house, chart.planets["Mars"].house),
                detail=f"the Moon and Mars are in {rel}",
                polarity=0,
                caveat=(
                    "Classically read as earning capacity rather than ease; several "
                    "authors attach a hard edge to how the money is made."
                ),
            )
        )

    # Adhi Yoga — benefics in the 6th, 7th, 8th from the Moon.
    adhi = [n for n in BENEFICS if _house_from_moon(chart, n) in (6, 7, 8)]
    if len(adhi) >= 2:
        out.append(
            Yoga(
                name="Adhi Yoga",
                rule=(
                    "Benefics (Jupiter, Venus, Mercury) occupying the 6th, 7th and "
                    "8th from the Moon."
                ),
                source="Phaladeepika ch. 6",
                planets=tuple(adhi),
                houses=tuple(sorted(chart.planets[n].house for n in adhi)),
                detail=(
                    f"{_and_join(adhi)} {_agree(adhi, 'occupies', 'occupy')} "
                    "the 6th to 8th from the Moon"
                ),
                polarity=1,
                caveat=(f"Some authors require all three benefics; {len(adhi)} qualify here."),
            )
        )

    # Shakata — Moon in the 6th, 8th or 12th from Jupiter.
    moon_from_jup = ((moon_idx - chart.planets["Jupiter"].sign_idx) % 12) + 1
    if moon_from_jup in DUSTHANA_HOUSES:
        cancelled = chart.planets["Moon"].house in KENDRA_HOUSES
        out.append(
            Yoga(
                name="Shakata Yoga",
                rule="The Moon occupying the 6th, 8th or 12th from Jupiter.",
                source="Saravali ch. 36",
                planets=("Moon", "Jupiter"),
                houses=(chart.planets["Moon"].house,),
                detail=f"the Moon stands in the {_ord(moon_from_jup)} from Jupiter",
                polarity=-1,
                caveat=(
                    "Cancelled here: the Moon occupies a kendra from the lagna, which "
                    "most authors treat as annulling Shakata."
                    if cancelled
                    else "No cancellation found; the Moon does not hold a kendra from the lagna."
                ),
            )
        )

    # Budhaditya — Sun with Mercury.
    if _same_sign(chart, "Sun", "Mercury"):
        sep = abs(
            (chart.planets["Mercury"].longitude - chart.planets["Sun"].longitude + 180) % 360 - 180
        )
        out.append(
            Yoga(
                name="Budhaditya Yoga",
                rule="Mercury and the Sun occupying the same sign.",
                source="Phaladeepika ch. 6",
                planets=("Sun", "Mercury"),
                houses=(chart.planets["Sun"].house,),
                detail=f"the Sun and Mercury share {chart.planets['Sun'].sign}, {sep:.1f}° apart",
                polarity=1,
                caveat=(
                    f"Mercury is combust at {sep:.1f}° from the Sun, and many authors "
                    "hold that combustion weakens or voids this yoga."
                    if sep <= 14.0
                    else None
                ),
            )
        )
    return out


def _kala_sarpa(chart: Chart) -> list[Yoga]:
    rahu = chart.planets["Rahu"].longitude
    offsets = {n: (chart.planets[n].longitude - rahu) % 360 for n in TRUE_PLANETS}
    forward = all(0.0 < d < 180.0 for d in offsets.values())
    backward = all(180.0 < d < 360.0 for d in offsets.values())
    if not (forward or backward):
        return []
    side = "between Rahu and Ketu in zodiacal order" if forward else "between Ketu and Rahu"
    return [
        Yoga(
            name="Kala Sarpa Yoga",
            rule="All seven true planets hemmed inside the Rahu-Ketu axis.",
            source=(
                "Not found in Brihat Parashara Hora Shastra, Phaladeepika, or "
                "Saravali. A twentieth-century construct of uncertain provenance."
            ),
            planets=("Rahu", "Ketu"),
            houses=(chart.planets["Rahu"].house, chart.planets["Ketu"].house),
            detail=f"all seven true planets fall {side}",
            polarity=0,
            caveat=(
                "Reported for completeness only. Because it has no classical source, "
                "it is not counted as supporting evidence for any claim."
            ),
            disputed=True,
        )
    ]


# ── public entry point ────────────────────────────────────────────────


@dataclass
class YogaReport:
    formed: list[Yoga] = field(default_factory=list)

    @property
    def auspicious(self) -> list[Yoga]:
        return [y for y in self.formed if y.polarity > 0 and not y.disputed]

    @property
    def challenging(self) -> list[Yoga]:
        return [y for y in self.formed if y.polarity < 0 and not y.disputed]

    @property
    def flagged(self) -> list[Yoga]:
        return [y for y in self.formed if y.disputed]

    def touching_house(self, house: int) -> list[Yoga]:
        return [y for y in self.formed if house in y.houses and not y.disputed]


def detect_yogas(chart: Chart) -> YogaReport:
    """Every yoga this module can prove from the chart, and nothing else."""
    pairs = _aspect_pairs(chart)
    formed: list[Yoga] = []
    formed += _raja_yogas(chart, pairs)
    formed += _dhana_yogas(chart, pairs)
    formed += _vipreeta_yogas(chart)
    formed += _neechabhanga(chart, pairs)
    formed += _parivartana(chart)
    formed += _mahapurusha(chart)
    formed += _lunar_yogas(chart, pairs)
    formed += _kala_sarpa(chart)
    return YogaReport(formed=formed)


# ── text helpers ──────────────────────────────────────────────────────


def _ord(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"


def _and_join(items: list[str]) -> str:
    if not items:
        return "nothing"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _agree(items: list[str], singular: str, plural: str) -> str:
    """Pick the verb form that agrees with a joined subject list."""
    return singular if len(items) == 1 else plural


__all__ = [
    "Yoga",
    "YogaReport",
    "detect_yogas",
    "house_sign",
    "occupants",
]
