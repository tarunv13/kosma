"""
Krishnamurti Paddhati significators and cuspal sub-lords.

KP's central claim is that a planet delivers the results of its *star lord*
rather than its own, and that the *sub lord* of a cusp decides whether the
matter of that house comes to pass. Both are mechanical once the star/sub/
sub-sub chain is known, which the base engine already computes.

The four-fold significator ordering (often written A, B, C, D) is:

  A — houses occupied by the planet's star lord
  B — houses owned by the planet's star lord
  C — houses occupied by the planet itself
  D — houses owned by the planet itself

A outranks B outranks C outranks D.

Note on house system
--------------------
KP is a cusp-based system and uses Placidus cusps, not whole-sign houses. The
base engine computes Placidus cusps alongside the whole-sign houses used
everywhere else in this codebase, and this module uses the Placidus cusps.
That means a planet's KP house can legitimately differ from its whole-sign
house, and both are reported rather than reconciled.

Source
------
* K. S. Krishnamurti, *Krishnamurti Paddhati* readers I-VI.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dignity import OWN_SIGNS, SIGN_LORDS
from .vedic_engine import SIGNS, VARA, VEDIC_PLANETS, Chart, kp_sublord, nakshatra_info, sign_info

KP_PLANETS = VEDIC_PLANETS

_VARA_LORD: dict[str, str] = {
    "Sunday": "Sun",
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
}


@dataclass(frozen=True)
class Cusp:
    """One Placidus house cusp with its KP chain."""

    house: int
    longitude: float
    sign: str
    deg_in_sign: float
    nakshatra: str
    star_lord: str
    sub_lord: str
    sub_sub_lord: str

    @property
    def chain(self) -> str:
        return f"{self.star_lord}/{self.sub_lord}/{self.sub_sub_lord}"


def cusps(chart: Chart) -> list[Cusp]:
    """The twelve Placidus cusps with their star, sub and sub-sub lords."""
    out: list[Cusp] = []
    raw = chart.house_cusps
    for h in range(1, 13):
        if len(raw) >= 12:
            lon = raw[h - 1] % 360.0
        else:  # fall back to equal houses if cusps were unavailable
            lon = (chart.ascendant_lon + (h - 1) * 30.0) % 360.0
        sign, deg, _ = sign_info(lon)
        nak, _pada, _deg_in, _lord = nakshatra_info(lon)
        star, sub, ss = kp_sublord(lon)
        out.append(
            Cusp(
                house=h,
                longitude=round(lon, 6),
                sign=sign,
                deg_in_sign=round(deg, 6),
                nakshatra=nak,
                star_lord=star,
                sub_lord=sub,
                sub_sub_lord=ss,
            )
        )
    return out


def kp_house_of(chart: Chart, longitude: float) -> int:
    """Placidus house holding a longitude, by cusp span rather than by sign."""
    raw = chart.house_cusps
    if len(raw) < 12:
        return ((int(longitude / 30) - chart.ascendant_sign_idx) % 12) + 1
    for h in range(12):
        start = raw[h] % 360.0
        end = raw[(h + 1) % 12] % 360.0
        span = (end - start) % 360.0
        offset = (longitude - start) % 360.0
        if offset < span:
            return h + 1
    return 12


@dataclass(frozen=True)
class Significator:
    """A planet's four-fold house significations."""

    planet: str
    star_lord: str
    occupied_by_star_lord: tuple[int, ...]  # A
    owned_by_star_lord: tuple[int, ...]  # B
    occupied_by_self: tuple[int, ...]  # C
    owned_by_self: tuple[int, ...]  # D

    @property
    def ranked(self) -> list[tuple[str, tuple[int, ...]]]:
        return [
            ("A", self.occupied_by_star_lord),
            ("B", self.owned_by_star_lord),
            ("C", self.occupied_by_self),
            ("D", self.owned_by_self),
        ]

    @property
    def all_houses(self) -> tuple[int, ...]:
        seen: list[int] = []
        for _, houses in self.ranked:
            for h in houses:
                if h not in seen:
                    seen.append(h)
        return tuple(seen)

    @property
    def summary(self) -> str:
        parts = [f"{tag}{list(h)}" for tag, h in self.ranked if h]
        return f"{self.planet} (star lord {self.star_lord}): " + " ".join(parts)


def _houses_owned(chart: Chart, planet: str) -> tuple[int, ...]:
    """Placidus houses whose cusp sign is ruled by ``planet``."""
    owned = OWN_SIGNS.get(planet, [])
    if not owned:
        return ()
    return tuple(c.house for c in cusps(chart) if c.sign in owned)


def significators(chart: Chart) -> dict[str, Significator]:
    """The ABCD significator table for every planet."""
    cusp_list = cusps(chart)
    kp_house: dict[str, int] = {
        name: kp_house_of(chart, chart.planets[name].longitude) for name in KP_PLANETS
    }
    owned_cache: dict[str, tuple[int, ...]] = {}

    def owned(p: str) -> tuple[int, ...]:
        if p not in owned_cache:
            owned_names = OWN_SIGNS.get(p, [])
            owned_cache[p] = tuple(c.house for c in cusp_list if c.sign in owned_names)
        return owned_cache[p]

    out: dict[str, Significator] = {}
    for name in KP_PLANETS:
        star = chart.planets[name].star_lord
        out[name] = Significator(
            planet=name,
            star_lord=star,
            occupied_by_star_lord=(kp_house[star],) if star in kp_house else (),
            owned_by_star_lord=owned(star),
            occupied_by_self=(kp_house[name],),
            owned_by_self=owned(name),
        )
    return out


def house_significators(chart: Chart) -> dict[int, dict[str, list[str]]]:
    """Inverse table: which planets signify each house, grouped by level."""
    sig = significators(chart)
    out: dict[int, dict[str, list[str]]] = {
        h: {"A": [], "B": [], "C": [], "D": []} for h in range(1, 13)
    }
    for planet, s in sig.items():
        for tag, houses in s.ranked:
            for h in houses:
                if planet not in out[h][tag]:
                    out[h][tag].append(planet)
    return out


def ruling_planets(chart: Chart) -> dict[str, str]:
    """The KP ruling planets for the chart's moment.

    Used in horary and birth-time rectification: the lords of the ascendant
    and Moon by sign and by star, plus the lord of the weekday.
    """
    asc_lon = chart.ascendant_lon
    asc_sign, _, _ = sign_info(asc_lon)
    _, _, _, asc_star = nakshatra_info(asc_lon)
    moon = chart.planets["Moon"]
    vara = VARA[int(chart.jd + 1.5) % 7]
    return {
        "lagna_sign_lord": SIGN_LORDS[asc_sign],
        "lagna_star_lord": asc_star,
        "lagna_sub_lord": chart.ascendant_kp[1],
        "moon_sign_lord": SIGN_LORDS[moon.sign],
        "moon_star_lord": moon.star_lord,
        "day_lord": _VARA_LORD[vara],
    }


# ── cuspal judgement ──────────────────────────────────────────────────

# KP judges a matter by whether the sub lord of the relevant cusp signifies
# the houses that support it. These are the standard house groupings; they
# describe what a house *is about*, not what will happen.
SUPPORTING_HOUSES: dict[str, tuple[int, ...]] = {
    "marriage": (2, 7, 11),
    "career": (2, 6, 10, 11),
    "wealth": (2, 6, 10, 11),
    "education": (4, 9, 11),
    "children": (2, 5, 11),
    "health": (1, 5, 11),
    "property": (4, 11, 12),
    "foreign travel": (3, 9, 12),
    "litigation": (6, 11),
}

OBSTRUCTING_HOUSES: dict[str, tuple[int, ...]] = {
    "marriage": (1, 6, 10),
    "career": (5, 8, 9, 12),
    "wealth": (5, 8, 9, 12),
    "education": (3, 5, 8),
    "children": (1, 4, 10),
    "health": (6, 8, 12),
    "property": (3, 8, 10),
    "foreign travel": (4, 8, 11),
    "litigation": (5, 8, 12),
}


@dataclass(frozen=True)
class CuspalVerdict:
    """What the sub lord of a cusp signifies for a named matter."""

    matter: str
    cusp: int
    sub_lord: str
    signifies: tuple[int, ...]
    supporting_hit: tuple[int, ...]
    obstructing_hit: tuple[int, ...]
    reading: str
    caveat: str


def judge_cusp(chart: Chart, matter: str, cusp_house: int) -> CuspalVerdict | None:
    """Report which supporting and obstructing houses a cusp's sub lord signifies.

    This deliberately stops at reporting. KP practitioners use this table to
    reach a yes/no, but that step depends on the question asked, the ruling
    planets at the moment of asking, and the dasha in force — none of which a
    natal chart alone supplies.
    """
    if matter not in SUPPORTING_HOUSES:
        return None
    cusp_list = cusps(chart)
    sub = cusp_list[cusp_house - 1].sub_lord
    sig = significators(chart)[sub]
    houses = set(sig.all_houses)
    support = tuple(sorted(houses & set(SUPPORTING_HOUSES[matter])))
    obstruct = tuple(sorted(houses & set(OBSTRUCTING_HOUSES[matter])))

    if support and not obstruct:
        reading = f"the sub lord signifies only supporting houses {list(support)}"
    elif obstruct and not support:
        reading = f"the sub lord signifies only obstructing houses {list(obstruct)}"
    elif support and obstruct:
        reading = (
            f"the sub lord signifies both supporting {list(support)} and "
            f"obstructing {list(obstruct)} houses — KP treats this as mixed"
        )
    else:
        reading = "the sub lord signifies neither the supporting nor the obstructing set"

    return CuspalVerdict(
        matter=matter,
        cusp=cusp_house,
        sub_lord=sub,
        signifies=sig.all_houses,
        supporting_hit=support,
        obstructing_hit=obstruct,
        reading=reading,
        caveat=(
            "Reported, not decided. A KP verdict also needs the ruling planets "
            "at the moment the question is asked and the dasha running then."
        ),
    )


def kp_summary(chart: Chart) -> dict[str, object]:
    """Everything this module knows, as plain data."""
    return {
        "house_system": "Placidus cusps (KP standard), distinct from the whole-sign houses used elsewhere",
        "cusps": [
            {
                "house": c.house,
                "sign": c.sign,
                "degree": round(c.deg_in_sign, 4),
                "nakshatra": c.nakshatra,
                "star_lord": c.star_lord,
                "sub_lord": c.sub_lord,
                "sub_sub_lord": c.sub_sub_lord,
            }
            for c in cusps(chart)
        ],
        "significators": {p: s.summary for p, s in significators(chart).items()},
        "house_significators": house_significators(chart),
        "ruling_planets": ruling_planets(chart),
    }


__all__ = [
    "SIGNS",
    "Cusp",
    "CuspalVerdict",
    "Significator",
    "cusps",
    "house_significators",
    "judge_cusp",
    "kp_house_of",
    "kp_summary",
    "ruling_planets",
    "significators",
]
