"""
Divisional charts (varga chakra), D1 through D60.

Each varga is a deterministic function from a sidereal longitude to a sign
index, following the Parashari construction rules. They are written out one at
a time rather than generated from a single formula, because they genuinely
differ: some step forward one sign per division, some jump by trines or
kendras, some start from a different sign depending on the parent sign's
modality or element, and D30 is not an equal division at all.

Sources
-------
* Brihat Parashara Hora Shastra ch. 6 (Shodasavarga) — the sixteen divisions,
  their construction, and the life area each governs.
* Saravali ch. 8 — Trimsamsa lordships.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .dignity import SIGN_LORDS
from .vedic_engine import SIGNS, VEDIC_PLANETS, Chart

# ── construction rules ────────────────────────────────────────────────


def _is_odd_sign(sign_idx: int) -> bool:
    """Aries is the 1st sign and therefore odd; index 0 is odd."""
    return sign_idx % 2 == 0


def _modality(sign_idx: int) -> int:
    """0 movable (chara), 1 fixed (sthira), 2 dual (dvisvabhava)."""
    return sign_idx % 3


def d1(sign_idx: int, deg: float) -> int:
    return sign_idx


def d2(sign_idx: int, deg: float) -> int:
    """Hora. Odd signs give Leo then Cancer; even signs the reverse."""
    first_half = deg < 15.0
    if _is_odd_sign(sign_idx):
        return 4 if first_half else 3  # Leo, then Cancer
    return 3 if first_half else 4  # Cancer, then Leo


def d3(sign_idx: int, deg: float) -> int:
    """Drekkana. The three parts fall in the sign's own trine."""
    return (sign_idx + 4 * int(deg / 10.0)) % 12


def d4(sign_idx: int, deg: float) -> int:
    """Chaturthamsa. The four parts fall in the sign's kendras."""
    return (sign_idx + 3 * int(deg / 7.5)) % 12


def d7(sign_idx: int, deg: float) -> int:
    """Saptamsa. Odd signs start from themselves, even from the 7th."""
    start = sign_idx if _is_odd_sign(sign_idx) else (sign_idx + 6) % 12
    return (start + int(deg / (30.0 / 7.0))) % 12


def d9(sign_idx: int, deg: float) -> int:
    """Navamsa. Starts from the first sign of the parent sign's element."""
    start = (12 - (sign_idx % 4) * 3) % 12
    return (start + int(deg / (30.0 / 9.0))) % 12


def d10(sign_idx: int, deg: float) -> int:
    """Dasamsa. Odd signs start from themselves, even from the 9th."""
    start = sign_idx if _is_odd_sign(sign_idx) else (sign_idx + 8) % 12
    return (start + int(deg / 3.0)) % 12


def d12(sign_idx: int, deg: float) -> int:
    """Dwadasamsa. Always starts from the sign itself."""
    return (sign_idx + int(deg / 2.5)) % 12


def d16(sign_idx: int, deg: float) -> int:
    """Shodasamsa. Movable from Aries, fixed from Leo, dual from Sagittarius."""
    start = (0, 4, 8)[_modality(sign_idx)]
    return (start + int(deg / 1.875)) % 12


def d20(sign_idx: int, deg: float) -> int:
    """Vimsamsa. Movable from Aries, fixed from Sagittarius, dual from Leo."""
    start = (0, 8, 4)[_modality(sign_idx)]
    return (start + int(deg / 1.5)) % 12


def d24(sign_idx: int, deg: float) -> int:
    """Chaturvimsamsa. Odd signs start from Leo, even from Cancer."""
    start = 4 if _is_odd_sign(sign_idx) else 3
    return (start + int(deg / 1.25)) % 12


def d27(sign_idx: int, deg: float) -> int:
    """Bhamsa. Starts from the first sign of the parent sign's element."""
    start = (sign_idx % 4) * 3
    return (start + int(deg / (30.0 / 27.0))) % 12


# Trimsamsa is the one unequal division: five uneven arcs ruled by the five
# non-luminary planets, running one way in odd signs and the other in even.
_TRIMSAMSA_ODD: tuple[tuple[float, int], ...] = (
    (5.0, 0),  # Mars      -> Aries
    (10.0, 10),  # Saturn   -> Aquarius
    (18.0, 8),  # Jupiter  -> Sagittarius
    (25.0, 2),  # Mercury  -> Gemini
    (30.0, 6),  # Venus    -> Libra
)
_TRIMSAMSA_EVEN: tuple[tuple[float, int], ...] = (
    (5.0, 1),  # Venus    -> Taurus
    (12.0, 5),  # Mercury  -> Virgo
    (20.0, 11),  # Jupiter -> Pisces
    (25.0, 9),  # Saturn   -> Capricorn
    (30.0, 7),  # Mars     -> Scorpio
)


def d30(sign_idx: int, deg: float) -> int:
    """Trimsamsa. Unequal fifths; the luminaries rule no trimsamsa."""
    table = _TRIMSAMSA_ODD if _is_odd_sign(sign_idx) else _TRIMSAMSA_EVEN
    for limit, target in table:
        if deg < limit:
            return target
    return table[-1][1]


def d40(sign_idx: int, deg: float) -> int:
    """Khavedamsa. Odd signs start from Aries, even from Libra."""
    start = 0 if _is_odd_sign(sign_idx) else 6
    return (start + int(deg / 0.75)) % 12


def d45(sign_idx: int, deg: float) -> int:
    """Akshavedamsa. Movable from Aries, fixed from Leo, dual from Sagittarius."""
    start = (0, 4, 8)[_modality(sign_idx)]
    return (start + int(deg / (30.0 / 45.0))) % 12


def d60(sign_idx: int, deg: float) -> int:
    """Shashtiamsa. Counted forward from the sign itself."""
    return (sign_idx + int(deg * 2.0)) % 12


@dataclass(frozen=True)
class VargaSpec:
    """One division: how to build it and what it is read for."""

    code: str
    name: str
    divisions: int
    domain: str
    fn: Callable[[int, float], int]
    note: str | None = None


VARGAS: tuple[VargaSpec, ...] = (
    VargaSpec("D1", "Rasi", 1, "the body and the whole life", d1),
    VargaSpec("D2", "Hora", 2, "wealth and resources", d2),
    VargaSpec("D3", "Drekkana", 3, "siblings, courage, initiative", d3),
    VargaSpec("D4", "Chaturthamsa", 4, "home, land, fixed fortune", d4),
    VargaSpec("D7", "Saptamsa", 7, "children and progeny", d7),
    VargaSpec("D9", "Navamsa", 9, "spouse, dharma, inner strength", d9),
    VargaSpec("D10", "Dasamsa", 10, "career and action in the world", d10),
    VargaSpec("D12", "Dwadasamsa", 12, "parents and ancestry", d12),
    VargaSpec("D16", "Shodasamsa", 16, "vehicles, comforts, contentment", d16),
    VargaSpec("D20", "Vimsamsa", 20, "spiritual practice and devotion", d20),
    VargaSpec("D24", "Chaturvimsamsa", 24, "learning and education", d24),
    VargaSpec("D27", "Bhamsa", 27, "raw strength and weakness", d27),
    VargaSpec(
        "D30",
        "Trimsamsa",
        30,
        "misfortune and affliction",
        d30,
        note="An unequal division; the Sun and Moon rule no trimsamsa.",
    ),
    VargaSpec("D40", "Khavedamsa", 40, "maternal legacy", d40),
    VargaSpec("D45", "Akshavedamsa", 45, "paternal legacy and conduct", d45),
    VargaSpec(
        "D60",
        "Shashtiamsa",
        60,
        "the finest karmic resolution",
        d60,
        note=(
            "Counted forward from the sign for both odd and even signs, per "
            "BPHS ch. 6. Some later authors reverse the count in even signs, "
            "which shifts every placement, so verify against your own "
            "tradition before leaning on D60."
        ),
    ),
)

VARGA_BY_CODE: dict[str, VargaSpec] = {v.code: v for v in VARGAS}

# The shadvarga, saptavarga and shodasavarga groupings used for varga strength.
SHADVARGA = ("D1", "D2", "D3", "D9", "D12", "D30")
SAPTAVARGA = ("D1", "D2", "D3", "D7", "D9", "D12", "D30")
SHODASAVARGA = tuple(v.code for v in VARGAS)


# ── chart construction ────────────────────────────────────────────────


@dataclass(frozen=True)
class VargaPosition:
    body: str
    sign: str
    sign_idx: int
    house: int  # from the varga ascendant
    lord: str


@dataclass(frozen=True)
class VargaChart:
    code: str
    name: str
    domain: str
    ascendant_sign: str
    ascendant_sign_idx: int
    positions: dict[str, VargaPosition]
    note: str | None = None

    def sign_of(self, body: str) -> str:
        return self.positions[body].sign


def build_varga(chart: Chart, code: str) -> VargaChart:
    """Build one divisional chart from the natal longitudes."""
    spec = VARGA_BY_CODE[code]
    asc_idx = spec.fn(chart.ascendant_sign_idx, chart.ascendant_deg)

    positions: dict[str, VargaPosition] = {}
    for name in VEDIC_PLANETS:
        p = chart.planets[name]
        sidx = spec.fn(p.sign_idx, p.deg_in_sign)
        positions[name] = VargaPosition(
            body=name,
            sign=SIGNS[sidx],
            sign_idx=sidx,
            house=((sidx - asc_idx) % 12) + 1,
            lord=SIGN_LORDS[SIGNS[sidx]],
        )

    return VargaChart(
        code=spec.code,
        name=spec.name,
        domain=spec.domain,
        ascendant_sign=SIGNS[asc_idx],
        ascendant_sign_idx=asc_idx,
        positions=positions,
        note=spec.note,
    )


def build_all_vargas(chart: Chart, codes: tuple[str, ...] = SHODASAVARGA) -> dict[str, VargaChart]:
    """Build every requested divisional chart."""
    return {code: build_varga(chart, code) for code in codes}


# ── varga strength (vimshopaka-style tally) ───────────────────────────


def vargottama(chart: Chart, body: str) -> bool:
    """True when a body holds the same sign in D1 and D9 — a strength marker."""
    p = chart.planets[body]
    return d9(p.sign_idx, p.deg_in_sign) == p.sign_idx


def varga_dignity_count(chart: Chart, body: str, group: tuple[str, ...] = SAPTAVARGA) -> dict:
    """Count how many divisions of ``group`` place ``body`` in a good sign.

    "Good" here means own sign, exaltation, or the sign of a natural friend —
    the same test the shadvarga tables use. This is a tally, not an
    interpretation: it says how consistently the divisions favour a planet.
    """
    from .dignity import EXALTATION, OWN_SIGNS, natural_relation

    p = chart.planets[body]
    strong: list[str] = []
    weak: list[str] = []
    for code in group:
        spec = VARGA_BY_CODE[code]
        sidx = spec.fn(p.sign_idx, p.deg_in_sign)
        sign = SIGNS[sidx]
        lord = SIGN_LORDS[sign]
        exalt = EXALTATION.get(body)
        if (
            sign in OWN_SIGNS.get(body, [])
            or (exalt and sign == exalt[0])
            or (body not in ("Rahu", "Ketu") and natural_relation(body, lord) == "friend")
        ):
            strong.append(code)
        elif (exalt and sign == SIGNS[(SIGNS.index(exalt[0]) + 6) % 12]) or (
            body not in ("Rahu", "Ketu") and natural_relation(body, lord) == "enemy"
        ):
            weak.append(code)

    return {
        "body": body,
        "group": list(group),
        "strong_in": strong,
        "weak_in": weak,
        "strong_count": len(strong),
        "weak_count": len(weak),
        "total": len(group),
        "vargottama": vargottama(chart, body),
    }
