"""
Planetary dignity, strength, and functional nature.

Every function here answers a *factual* question about a placement — "is Mars
exalted?", "is Mercury combust?", "does Saturn rule a kendra and a trikona?" —
so that the evidence layer can cite an answer instead of inventing one. Nothing
in this module interprets, predicts, or advises.

Where classical traditions genuinely disagree (the nodes' exaltation signs, the
winner of a planetary war) the disagreement is recorded on the result and
flagged ``disputed``. The confirmation gate in :mod:`kosma.evidence` refuses to
count a disputed item as supporting evidence.

Sources
-------
* Brihat Parashara Hora Shastra ch. 3-4 — exaltation, own signs, moolatrikona,
  natural (naisargika) friendship.
* Phaladeepika ch. 2 — temporal (tatkalika) and compound (panchadha) relations.
* Brihat Parashara Hora Shastra ch. 6 — combustion (astangata) orbs.
* Brihat Parashara Hora Shastra ch. 27 (Shadbala) — directional strength
  (dig bala) and motional strength (cheshta bala).
"""

from __future__ import annotations

from dataclasses import dataclass

from .vedic_engine import LAGNA_LORDS, SIGNS, Chart

# ── Sign rulership ────────────────────────────────────────────────────

SIGN_LORDS = LAGNA_LORDS  # sign name -> ruling planet (BPHS ch. 3)

OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

# ── Exaltation / debilitation (BPHS ch. 3) ────────────────────────────
# (sign, exact degree of deepest exaltation). Debilitation is the opposite
# sign at the same degree.

EXALTATION: dict[str, tuple[str, float]] = {
    "Sun": ("Aries", 10.0),
    "Moon": ("Taurus", 3.0),
    "Mars": ("Capricorn", 28.0),
    "Mercury": ("Virgo", 15.0),
    "Jupiter": ("Cancer", 5.0),
    "Venus": ("Pisces", 27.0),
    "Saturn": ("Libra", 20.0),
}

# The nodes have no undisputed exaltation. BPHS is silent; later authors
# variously assign Rahu to Taurus or Gemini and Ketu to Scorpio or
# Sagittarius. Recorded for transparency, never counted as evidence.
DISPUTED_NODE_EXALTATION: dict[str, str] = {
    "Rahu": "Taurus or Gemini depending on the author; BPHS assigns none.",
    "Ketu": "Scorpio or Sagittarius depending on the author; BPHS assigns none.",
}

# ── Moolatrikona ranges (BPHS ch. 3), degrees within the sign ─────────

MOOLATRIKONA: dict[str, tuple[str, float, float]] = {
    "Sun": ("Leo", 0.0, 20.0),
    "Moon": ("Taurus", 4.0, 30.0),
    "Mars": ("Aries", 0.0, 12.0),
    "Mercury": ("Virgo", 16.0, 20.0),
    "Jupiter": ("Sagittarius", 0.0, 10.0),
    "Venus": ("Libra", 0.0, 15.0),
    "Saturn": ("Aquarius", 0.0, 20.0),
}

# ── Natural (naisargika) relations, BPHS ch. 3 ────────────────────────

_FRIENDS: dict[str, set[str]] = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

_ENEMIES: dict[str, set[str]] = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}

# ── Combustion orbs in degrees from the Sun (BPHS ch. 6) ──────────────
# (orb when direct, orb when retrograde)

COMBUSTION_ORB: dict[str, tuple[float, float]] = {
    "Moon": (12.0, 12.0),
    "Mars": (17.0, 17.0),
    "Mercury": (14.0, 12.0),
    "Jupiter": (11.0, 11.0),
    "Venus": (10.0, 8.0),
    "Saturn": (15.0, 15.0),
}

# ── Directional strength, dig bala (BPHS ch. 27) ──────────────────────

DIG_BALA_HOUSE: dict[str, int] = {
    "Jupiter": 1,
    "Mercury": 1,
    "Sun": 10,
    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
}

NATURAL_BENEFICS = {"Jupiter", "Venus"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

KENDRAS = (1, 4, 7, 10)
TRIKONAS = (1, 5, 9)
DUSTHANAS = (6, 8, 12)
UPACHAYAS = (3, 6, 10, 11)
MARAKAS = (2, 7)

# Canonical dignity states, ordered strongest to weakest.
_STATE_SCORE: dict[str, float] = {
    "exalted": 2.0,
    "moolatrikona": 1.75,
    "own sign": 1.5,
    "great friend's sign": 1.0,
    "friend's sign": 0.5,
    "neutral sign": 0.0,
    "enemy's sign": -0.5,
    "great enemy's sign": -1.0,
    "debilitated": -2.0,
}


# ── Relations ─────────────────────────────────────────────────────────


def natural_relation(a: str, b: str) -> str:
    """Permanent friendship of ``a`` toward ``b`` (BPHS ch. 3)."""
    if a == b:
        return "own"
    if b in _FRIENDS.get(a, set()):
        return "friend"
    if b in _ENEMIES.get(a, set()):
        return "enemy"
    return "neutral"


def temporal_relation(chart: Chart, a: str, b: str) -> str:
    """Temporary friendship of ``a`` toward ``b`` (Phaladeepika ch. 2).

    A planet in the 2nd, 3rd, 4th, 10th, 11th or 12th sign from another is its
    temporal friend; one in the 1st, 5th, 6th, 7th, 8th or 9th is its temporal
    enemy.
    """
    sa = chart.planets[a].sign_idx
    sb = chart.planets[b].sign_idx
    distance = ((sb - sa) % 12) + 1
    return "friend" if distance in (2, 3, 4, 10, 11, 12) else "enemy"


# natural x temporal -> compound (panchadha maitri), Phaladeepika ch. 2
_COMPOUND: dict[tuple[str, str], str] = {
    ("friend", "friend"): "great friend",
    ("friend", "enemy"): "neutral",
    ("neutral", "friend"): "friend",
    ("neutral", "enemy"): "enemy",
    ("enemy", "friend"): "neutral",
    ("enemy", "enemy"): "great enemy",
}


def compound_relation(chart: Chart, a: str, b: str) -> str:
    """Five-fold (panchadha) relation of ``a`` toward ``b``."""
    if a == b:
        return "own"
    nat = natural_relation(a, b)
    tmp = temporal_relation(chart, a, b)
    return _COMPOUND[(nat, tmp)]


# ── Functional nature for a given ascendant ───────────────────────────


def houses_ruled(chart: Chart, planet: str) -> list[int]:
    """Houses (from the natal lagna) ruled by ``planet``. Nodes rule none."""
    asc = chart.ascendant_sign_idx
    return sorted(((SIGNS.index(s) - asc) % 12) + 1 for s in OWN_SIGNS.get(planet, []))


def functional_nature(chart: Chart, planet: str) -> tuple[str, str]:
    """Return (nature, reason) for ``planet`` relative to the natal lagna.

    Parashari functional rules: trikona lords are auspicious, lords of 3/6/11
    are inauspicious, lords of 8 and 12 are inauspicious, and a planet ruling
    both a kendra and a trikona is a yogakaraka. The nodes rule no sign and
    take the nature of their dispositor's house context, so they are reported
    as ``contextual``.
    """
    if planet in ("Rahu", "Ketu"):
        return (
            "contextual",
            "The nodes own no sign, so they carry no fixed functional nature; "
            "BPHS gives them the results of their dispositor and their house.",
        )

    ruled = houses_ruled(chart, planet)
    has_kendra = any(h in (4, 7, 10) for h in ruled)
    # The lagna is both a kendra and a trikona, so it cannot on its own make a
    # planet a yogakaraka — otherwise every lagna lord that also held a kendra
    # would qualify. Only the 5th and 9th count here, which yields exactly the
    # classical set: Mars for Cancer and Leo, Venus for Capricorn and Aquarius,
    # Saturn for Taurus and Libra.
    has_true_trikona = any(h in (5, 9) for h in ruled)

    if has_kendra and has_true_trikona:
        return (
            "yogakaraka",
            f"rules both a kendra and a trikona from the lagna (houses {_join(ruled)})",
        )
    if any(h in (1, 5, 9) for h in ruled):
        return "benefic", f"rules a trikona from the lagna (houses {_join(ruled)})"
    if any(h in (3, 6, 8, 11, 12) for h in ruled):
        bad = [h for h in ruled if h in (3, 6, 8, 11, 12)]
        return "malefic", f"rules {_join(bad)} from the lagna"
    if has_kendra and planet in NATURAL_BENEFICS | {"Mercury"}:
        return (
            "neutral",
            f"rules only kendras (houses {_join(ruled)}); a natural benefic owning "
            "kendras alone takes on kendradhipati dosha and loses its benefic edge",
        )
    return "neutral", f"rules houses {_join(ruled)} from the lagna"


def _join(nums: list[int]) -> str:
    return ", ".join(str(n) for n in nums) if nums else "none"


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


# ── Contextual benefic / malefic ──────────────────────────────────────


def is_natural_benefic(chart: Chart, planet: str) -> tuple[bool, str]:
    """Natural benefic status, including the two contextual classical rules.

    The Moon is benefic while bright and malefic while dark; Mercury takes the
    nature of whatever it sits with (BPHS ch. 4).
    """
    if planet in NATURAL_BENEFICS:
        return True, "natural benefic"
    if planet == "Moon":
        elong = (chart.planets["Moon"].longitude - chart.planets["Sun"].longitude) % 360
        bright = 72.0 <= elong <= 288.0
        return bright, (
            f"Moon {'bright' if bright else 'dark'} at {elong:.1f}° from the Sun "
            f"({'benefic' if bright else 'malefic'} by BPHS ch. 4)"
        )
    if planet == "Mercury":
        sign_idx = chart.planets["Mercury"].sign_idx
        companions = [
            n
            for n, p in chart.planets.items()
            if n != "Mercury" and p.sign_idx == sign_idx and n in NATURAL_MALEFICS
        ]
        if companions:
            return False, f"Mercury sits with {_names(companions)}, taking a malefic tone"
        return True, "Mercury unafflicted by malefic company, so benefic"
    return False, "natural malefic"


def _names(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# ── The dignity record ────────────────────────────────────────────────


@dataclass(frozen=True)
class Dignity:
    """A fully-sourced strength record for one planet in one chart."""

    planet: str
    sign: str
    house: int
    state: str  # canonical dignity state, e.g. "exalted"
    state_reason: str
    benefic: bool
    benefic_reason: str
    functional: str  # yogakaraka / benefic / malefic / neutral / contextual
    functional_reason: str
    houses_ruled: list[int]
    combust: bool
    combust_note: str | None
    retrograde: bool
    dig_bala: bool
    planetary_war_with: str | None
    deep_note: str | None
    disputed: list[str]
    score: float

    @property
    def state_phrase(self) -> str:
        """The dignity state as a predicate, e.g. "in a great enemy's sign"."""
        if self.state in ("exalted", "debilitated"):
            return self.state
        if self.state == "moolatrikona":
            return "in moolatrikona"
        if self.state == "own sign":
            return "in its own sign"
        return f"in {_article(self.state)} {self.state}"

    @property
    def summary(self) -> str:
        bits = [f"{self.planet} in {self.sign} (H{self.house}), {self.state}"]
        if self.combust:
            bits.append("combust")
        if self.retrograde:
            bits.append("retrograde")
        if self.dig_bala:
            bits.append("with directional strength")
        if self.functional in ("yogakaraka", "benefic", "malefic"):
            bits.append(f"functionally {self.functional}")
        return ", ".join(bits)


def _dignity_state(planet: str, sign: str, deg_in_sign: float, chart: Chart) -> tuple[str, str]:
    """Resolve the canonical dignity state and the reason for it."""
    exalt = EXALTATION.get(planet)
    if exalt:
        ex_sign, ex_deg = exalt
        if sign == ex_sign:
            return "exalted", f"{ex_sign} is the exaltation sign (deepest at {ex_deg:.0f}°)"
        deb_sign = SIGNS[(SIGNS.index(ex_sign) + 6) % 12]
        if sign == deb_sign:
            return (
                "debilitated",
                f"{deb_sign} is the debilitation sign, opposite exaltation in {ex_sign}",
            )

    mt = MOOLATRIKONA.get(planet)
    if mt and sign == mt[0] and mt[1] <= deg_in_sign < mt[2]:
        return (
            "moolatrikona",
            f"{sign} {mt[1]:.0f}°-{mt[2]:.0f}° is the moolatrikona range",
        )

    if sign in OWN_SIGNS.get(planet, []):
        return "own sign", f"{planet} rules {sign}"

    lord = SIGN_LORDS[sign]
    if planet in ("Rahu", "Ketu"):
        return (
            "neutral sign",
            f"{sign} is ruled by {lord}; the nodes are assigned no friendship table in BPHS",
        )

    rel = compound_relation(chart, planet, lord)
    mapping = {
        "great friend": "great friend's sign",
        "friend": "friend's sign",
        "neutral": "neutral sign",
        "enemy": "enemy's sign",
        "great enemy": "great enemy's sign",
    }
    state = mapping[rel]
    nat = natural_relation(planet, lord)
    tmp = temporal_relation(chart, planet, lord)
    return state, (
        f"dispositor {lord} is {_article(nat)} {nat} by nature and a temporal "
        f"{tmp}, compounding to {rel} (panchadha maitri)"
    )


def _combustion(chart: Chart, planet: str) -> tuple[bool, str | None]:
    if planet not in COMBUSTION_ORB:
        return False, None
    sun = chart.planets["Sun"]
    p = chart.planets[planet]
    sep = abs((p.longitude - sun.longitude + 180) % 360 - 180)
    direct_orb, retro_orb = COMBUSTION_ORB[planet]
    orb = retro_orb if p.retrograde else direct_orb
    if sep <= orb:
        return True, (
            f"{sep:.2f}° from the Sun, inside the {orb:.0f}° combustion orb for "
            f"{'retrograde ' if p.retrograde else ''}{planet}"
        )
    return False, f"{sep:.2f}° from the Sun, outside the {orb:.0f}° combustion orb"


def _planetary_war(chart: Chart, planet: str) -> tuple[str | None, list[str]]:
    """Graha yuddha: two true planets within one degree of longitude."""
    if planet in ("Sun", "Moon", "Rahu", "Ketu"):
        return None, []
    p = chart.planets[planet]
    for other in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        if other == planet:
            continue
        q = chart.planets[other]
        sep = abs((p.longitude - q.longitude + 180) % 360 - 180)
        if sep <= 1.0:
            return other, [
                "The victor of a planetary war is decided differently by different "
                "authors (by northern latitude, by brightness, or by lower longitude), "
                "so no winner is asserted here."
            ]
    return None, []


def dignity_of(chart: Chart, planet: str) -> Dignity:
    """Build the complete, sourced dignity record for one planet."""
    p = chart.planets[planet]
    state, state_reason = _dignity_state(planet, p.sign, p.deg_in_sign, chart)
    benefic, benefic_reason = is_natural_benefic(chart, planet)
    functional, functional_reason = functional_nature(chart, planet)
    combust, combust_note = _combustion(chart, planet)
    war_with, disputed = _planetary_war(chart, planet)
    dig = DIG_BALA_HOUSE.get(planet) == p.house

    disputed = list(disputed)
    if planet in DISPUTED_NODE_EXALTATION:
        disputed.append(
            f"{planet} exaltation is unsettled: {DISPUTED_NODE_EXALTATION[planet]} "
            "No exaltation or debilitation is claimed for it here."
        )

    deep_note = None
    exalt = EXALTATION.get(planet)
    if exalt and p.sign == exalt[0] and abs(p.deg_in_sign - exalt[1]) <= 1.0:
        deep_note = f"within 1° of exact exaltation ({exalt[1]:.0f}° {exalt[0]})"
    elif exalt:
        deb_sign = SIGNS[(SIGNS.index(exalt[0]) + 6) % 12]
        if p.sign == deb_sign and abs(p.deg_in_sign - exalt[1]) <= 1.0:
            deep_note = f"within 1° of exact debilitation ({exalt[1]:.0f}° {deb_sign})"

    score = _STATE_SCORE.get(state, 0.0)
    if combust:
        score -= 1.0
    if dig:
        score += 0.5
    if p.retrograde and planet not in ("Rahu", "Ketu"):
        score += 0.25  # cheshta bala, BPHS ch. 27
    if war_with:
        score -= 0.25
    score = max(-2.5, min(2.5, score))

    return Dignity(
        planet=planet,
        sign=p.sign,
        house=p.house,
        state=state,
        state_reason=state_reason,
        benefic=benefic,
        benefic_reason=benefic_reason,
        functional=functional,
        functional_reason=functional_reason,
        houses_ruled=houses_ruled(chart, planet),
        combust=combust,
        combust_note=combust_note,
        retrograde=p.retrograde,
        dig_bala=dig,
        planetary_war_with=war_with,
        deep_note=deep_note,
        disputed=disputed,
        score=round(score, 3),
    )


def all_dignities(chart: Chart) -> dict[str, Dignity]:
    """Dignity records for all nine grahas, keyed by planet name."""
    return {name: dignity_of(chart, name) for name in chart.planets}
