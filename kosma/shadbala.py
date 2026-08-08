"""
Shadbala — the six-fold strength measure.

Strength is reported in virupas (sixtieths); sixty virupas make one rupa.

Honesty about completeness
--------------------------
Shadbala has more sub-components than any two authors agree on. This module
computes the ones that can be derived unambiguously from the chart and states
plainly which it leaves out, rather than quietly padding a total. Every
:class:`Shadbala` result carries an ``omitted`` list and a ``complete`` flag.

Included: uchcha, saptavargaja, ojhayugma, kendradi and drekkana (sthana bala);
dig bala; nathonnatha, paksha, tribhaga, vara, hora and ayana (kala bala);
cheshta bala; naisargika bala; drik bala.

Omitted: varsha and masa bala (they need a Hindu luni-solar calendar the rest
of this engine does not carry) and yuddha bala (the victor of a planetary war
is not asserted anywhere in this codebase). Because of those omissions, totals
run slightly below a textbook figure and should not be compared to the
classical minimum-strength thresholds as though they were complete. The
thresholds are reported alongside for reference only.

Sources
-------
* Brihat Parashara Hora Shastra ch. 27 (Shadbala).
* Saravali ch. 4 — naisargika ordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import swisseph as swe

from .dignity import (
    EXALTATION,
    MOOLATRIKONA,
    OWN_SIGNS,
    SIGN_LORDS,
    compound_relation,
)
from .vedic_engine import PLANETS, SIGNS, VARA, Chart

SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Naisargika bala is a fixed ranking by apparent brightness (BPHS ch. 27).
NAISARGIKA: dict[str, float] = {
    "Sun": 60.0,
    "Moon": 51.43,
    "Venus": 42.86,
    "Jupiter": 34.29,
    "Mercury": 25.71,
    "Mars": 17.14,
    "Saturn": 8.57,
}

# Classical minimum strength in rupas for a planet to deliver its promise.
REQUIRED_RUPAS: dict[str, float] = {
    "Sun": 5.0,
    "Moon": 6.0,
    "Mars": 5.0,
    "Mercury": 7.0,
    "Jupiter": 6.5,
    "Venus": 5.5,
    "Saturn": 5.0,
}

# Saptavargaja values by compound dignity (BPHS ch. 27).
_SAPTAVARGAJA: dict[str, float] = {
    "moolatrikona": 45.0,
    "own": 30.0,
    "great friend": 22.5,
    "friend": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "great enemy": 1.875,
}

_SAPTAVARGA_CODES = ("D1", "D2", "D3", "D7", "D9", "D12", "D30")

# Odd/even preference for ojhayugma bala.
_EVEN_LOVERS = ("Moon", "Venus")

# Gender classes for drekkana bala.
_MALE = ("Sun", "Mars", "Jupiter")
_FEMALE = ("Moon", "Venus")
_NEUTER = ("Mercury", "Saturn")

# Dig bala: the house whose cusp gives each planet full directional strength.
_DIG_STRONG_HOUSE: dict[str, int] = {
    "Jupiter": 1,
    "Mercury": 1,
    "Sun": 10,
    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
}

# Day-strong vs night-strong for nathonnatha bala; Mercury is always full.
_DAY_STRONG = ("Sun", "Jupiter", "Venus")
_NIGHT_STRONG = ("Moon", "Mars", "Saturn")

# Tribhaga lords: the three parts of the day, then the three of the night.
_TRIBHAGA_DAY = ("Mercury", "Sun", "Saturn")
_TRIBHAGA_NIGHT = ("Moon", "Venus", "Mars")

# Chaldean order, used to walk the planetary hours.
_CHALDEAN = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")
_VARA_LORD: dict[str, str] = {
    "Sunday": "Sun",
    "Monday": "Moon",
    "Tuesday": "Mars",
    "Wednesday": "Mercury",
    "Thursday": "Jupiter",
    "Friday": "Venus",
    "Saturday": "Saturn",
}

# Planets strong in northern declination for ayana bala; Moon and Saturn
# prefer the south, and Mercury benefits from either.
_NORTH_STRONG = ("Sun", "Mars", "Jupiter", "Venus")
_MAX_DECLINATION = 23.4392911  # obliquity of the ecliptic

# Discrete Parashari drishti grading used for drik bala. The continuous
# "sputa drishti" formula in some editions gives slightly different numbers;
# the discrete grading is used here because it matches the aspect rules the
# rest of this engine applies.
_DRISHTI_VALUE: dict[int, float] = {7: 60.0, 4: 45.0, 8: 45.0, 5: 30.0, 9: 30.0, 3: 15.0, 10: 15.0}
_SPECIAL_FULL: dict[str, tuple[int, ...]] = {
    "Mars": (4, 8),
    "Jupiter": (5, 9),
    "Saturn": (3, 10),
}
_BENEFIC_FOR_DRIK = ("Jupiter", "Venus", "Mercury", "Moon")


@dataclass
class Shadbala:
    """The six strengths for one planet, each component kept separate."""

    planet: str
    sthana: float
    dig: float
    kala: float
    cheshta: float
    naisargika: float
    drik: float
    breakdown: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    omitted: list[str] = field(default_factory=list)
    complete: bool = False

    @property
    def total_virupas(self) -> float:
        return round(
            self.sthana + self.dig + self.kala + self.cheshta + self.naisargika + self.drik, 2
        )

    @property
    def total_rupas(self) -> float:
        return round(self.total_virupas / 60.0, 3)

    @property
    def required_rupas(self) -> float:
        return REQUIRED_RUPAS[self.planet]

    @property
    def ratio(self) -> float:
        """Strength as a fraction of the classical requirement."""
        return round(self.total_rupas / self.required_rupas, 3)

    @property
    def verdict(self) -> str:
        """A band, not a prediction — and explicitly provisional."""
        r = self.ratio
        if r >= 1.25:
            return "strong"
        if r >= 1.0:
            return "adequate"
        if r >= 0.75:
            return "marginal"
        return "weak"


# ── sthana bala ───────────────────────────────────────────────────────


def _uchcha_bala(chart: Chart, planet: str) -> float:
    """Distance from the debilitation point, scaled to 0-60."""
    exalt = EXALTATION.get(planet)
    if not exalt:
        return 0.0
    ex_sign, ex_deg = exalt
    exalt_lon = SIGNS.index(ex_sign) * 30.0 + ex_deg
    deb_lon = (exalt_lon + 180.0) % 360.0
    arc = abs((chart.planets[planet].longitude - deb_lon + 180.0) % 360.0 - 180.0)
    return arc / 3.0


def _saptavargaja_bala(chart: Chart, planet: str) -> float:
    from .vargas import VARGA_BY_CODE

    if planet not in SEVEN:
        return 0.0
    p = chart.planets[planet]
    total = 0.0
    for code in _SAPTAVARGA_CODES:
        spec = VARGA_BY_CODE[code]
        sidx = spec.fn(p.sign_idx, p.deg_in_sign)
        sign = SIGNS[sidx]
        mt = MOOLATRIKONA.get(planet)
        if mt and sign == mt[0] and code == "D1" and mt[1] <= p.deg_in_sign < mt[2]:
            total += _SAPTAVARGAJA["moolatrikona"]
        elif sign in OWN_SIGNS.get(planet, []):
            total += _SAPTAVARGAJA["own"]
        else:
            rel = compound_relation(chart, planet, SIGN_LORDS[sign])
            total += _SAPTAVARGAJA.get(rel, 7.5)
    return total


def _ojhayugma_bala(chart: Chart, planet: str) -> float:
    """Fifteen for a favourable odd/even rasi, fifteen more for the navamsa."""
    from .vargas import d9

    if planet not in SEVEN:
        return 0.0
    p = chart.planets[planet]
    wants_even = planet in _EVEN_LOVERS
    total = 0.0
    rasi_even = p.sign_idx % 2 == 1
    if rasi_even == wants_even:
        total += 15.0
    nav_even = d9(p.sign_idx, p.deg_in_sign) % 2 == 1
    if nav_even == wants_even:
        total += 15.0
    return total


def _kendradi_bala(chart: Chart, planet: str) -> float:
    house = chart.planets[planet].house
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana_bala(chart: Chart, planet: str) -> float:
    """Fifteen for sitting in the drekkana matching the planet's gender class."""
    deg = chart.planets[planet].deg_in_sign
    third = int(deg / 10.0)  # 0, 1 or 2
    if planet in _MALE and third == 0:
        return 15.0
    if planet in _FEMALE and third == 1:
        return 15.0
    if planet in _NEUTER and third == 2:
        return 15.0
    return 0.0


# ── dig bala ──────────────────────────────────────────────────────────


def _dig_bala(chart: Chart, planet: str) -> float:
    house = _DIG_STRONG_HOUSE.get(planet)
    if house is None:
        return 0.0
    cusps = chart.house_cusps
    if len(cusps) >= 10:
        strong_lon = cusps[house - 1]
    else:  # fall back to equal houses from the lagna
        strong_lon = (chart.ascendant_lon + (house - 1) * 30.0) % 360.0
    weak_lon = (strong_lon + 180.0) % 360.0
    arc = abs((chart.planets[planet].longitude - weak_lon + 180.0) % 360.0 - 180.0)
    return arc / 3.0


# ── kala bala ─────────────────────────────────────────────────────────


def _sunrise_sunset(chart: Chart) -> tuple[float, float, bool]:
    """Local sunrise and sunset in hours, plus whether they were computed.

    Falls back to a flat 06:00/18:00 at latitudes where the Sun does not rise
    or set, and reports which happened.
    """
    try:
        day_start = float(int(chart.jd - 0.5)) + 0.5
        geo = (chart.lon_geo, chart.lat, 0.0)
        rc_r, t_rise = swe.rise_trans(day_start, swe.SUN, swe.CALC_RISE, geo)
        rc_s, t_set = swe.rise_trans(day_start, swe.SUN, swe.CALC_SET, geo)
        if rc_r == 0 and rc_s == 0:
            rise = (((t_rise[0] + 0.5) % 1.0) * 24.0 + chart.tz) % 24.0
            sset = (((t_set[0] + 0.5) % 1.0) * 24.0 + chart.tz) % 24.0
            return rise, sset, True
    except Exception:  # pragma: no cover - platform/ephemeris dependent
        pass
    return 6.0, 18.0, False


def _nathonnatha_bala(chart: Chart, planet: str) -> float:
    if planet == "Mercury":
        return 60.0
    h = chart.local_hour
    from_noon = abs(h - 12.0) / 12.0  # 0 at noon, 1 at midnight
    if planet in _DAY_STRONG:
        return 60.0 * (1.0 - from_noon)
    if planet in _NIGHT_STRONG:
        return 60.0 * from_noon
    return 0.0


def _paksha_bala(chart: Chart, planet: str) -> float:
    from .dignity import is_natural_benefic

    elong = (chart.planets["Moon"].longitude - chart.planets["Sun"].longitude) % 360.0
    if elong > 180.0:
        elong = 360.0 - elong
    bright = elong / 3.0  # 0-60
    benefic, _ = is_natural_benefic(chart, planet)
    value = bright if benefic else 60.0 - bright
    if planet == "Moon":
        value *= 2.0  # the Moon's paksha bala is doubled (BPHS ch. 27)
    return value


def _tribhaga_bala(chart: Chart, planet: str, rise: float, sset: float) -> float:
    if planet == "Jupiter":
        return 60.0  # Jupiter always receives tribhaga bala
    h = chart.local_hour
    if rise <= h < sset:
        part = int((h - rise) / max((sset - rise) / 3.0, 1e-9))
        lord = _TRIBHAGA_DAY[min(part, 2)]
    else:
        night_len = (24.0 - sset) + rise
        since = (h - sset) % 24.0
        part = int(since / max(night_len / 3.0, 1e-9))
        lord = _TRIBHAGA_NIGHT[min(part, 2)]
    return 60.0 if planet == lord else 0.0


def _vara_hora_bala(chart: Chart, planet: str, rise: float) -> tuple[float, float]:
    """Weekday lord scores 45; the lord of the birth hora scores 60."""
    vara = VARA[int(chart.jd + 1.5) % 7]
    day_lord = _VARA_LORD[vara]
    vara_bala = 45.0 if planet == day_lord else 0.0

    hours_since_rise = (chart.local_hour - rise) % 24.0
    hora_index = int(hours_since_rise)
    start = _CHALDEAN.index(day_lord)
    hora_lord = _CHALDEAN[(start + hora_index) % 7]
    hora_bala = 60.0 if planet == hora_lord else 0.0
    return vara_bala, hora_bala


def _declination(jd: float, planet: str) -> float:
    pid = PLANETS.get(planet)
    if planet == "Ketu":
        return -_declination(jd, "Rahu")
    if pid is None:
        return 0.0
    res, _ = swe.calc_ut(jd, pid, swe.FLG_EQUATORIAL)
    return float(res[1])


def _ayana_bala(chart: Chart, planet: str) -> float:
    dec = _declination(chart.jd, planet)
    if planet == "Mercury":
        effective = abs(dec)
    elif planet in _NORTH_STRONG:
        effective = dec
    else:
        effective = -dec
    value = 60.0 * (_MAX_DECLINATION + effective) / (2.0 * _MAX_DECLINATION)
    value = max(0.0, min(60.0, value))
    if planet == "Sun":
        value *= 2.0  # the Sun's ayana bala is doubled (BPHS ch. 27)
    return value


# ── cheshta bala ──────────────────────────────────────────────────────

# Mean daily motion in degrees, used to classify motion state.
_MEAN_SPEED: dict[str, float] = {
    "Mars": 0.5240,
    "Mercury": 4.0923,
    "Jupiter": 0.0831,
    "Venus": 1.6021,
    "Saturn": 0.0335,
}

# Motion states and their classical values (BPHS ch. 27).
_MOTION_VALUE: dict[str, float] = {
    "vakra (retrograde)": 60.0,
    "anuvakra (retrograde into the previous sign)": 30.0,
    "vikala (stationary)": 15.0,
    "mandatara (very slow)": 7.5,
    "manda (slow)": 15.0,
    "sama (mean speed)": 30.0,
    "chara (fast)": 30.0,
    "atichara (very fast)": 45.0,
}


def _cheshta_bala(chart: Chart, planet: str) -> tuple[float, str]:
    """Motional strength.

    The Sun and Moon take their ayana and paksha values by convention. The five
    star planets are classified into motion states by comparing actual daily
    speed with mean speed — a standard approximation, since the exact classical
    method needs the planet's mean longitude from the sighrocca.
    """
    if planet == "Sun":
        return _ayana_bala(chart, "Sun"), "the Sun's cheshta bala is its ayana bala"
    if planet == "Moon":
        return _paksha_bala(chart, "Moon"), "the Moon's cheshta bala is its paksha bala"
    if planet in ("Rahu", "Ketu"):
        return 0.0, "the nodes are assigned no cheshta bala"

    speed = chart.planets[planet].speed
    mean = _MEAN_SPEED[planet]
    if speed < 0:
        state = "vakra (retrograde)"
    elif abs(speed) < mean * 0.05:
        state = "vikala (stationary)"
    elif speed < mean * 0.5:
        state = "mandatara (very slow)"
    elif speed < mean * 0.9:
        state = "manda (slow)"
    elif speed <= mean * 1.1:
        state = "sama (mean speed)"
    elif speed <= mean * 1.5:
        state = "chara (fast)"
    else:
        state = "atichara (very fast)"
    return _MOTION_VALUE[
        state
    ], f"moving at {speed:.4f}°/day against a mean of {mean:.4f} — {state}"


# ── drik bala ─────────────────────────────────────────────────────────


def _drik_bala(chart: Chart, planet: str) -> float:
    """Net aspectual strength: benefic drishti minus malefic, quartered."""
    target_sign = chart.planets[planet].sign_idx
    net = 0.0
    for other in SEVEN:
        if other == planet:
            continue
        source_sign = chart.planets[other].sign_idx
        distance = ((target_sign - source_sign) % 12) + 1
        if distance in _SPECIAL_FULL.get(other, ()):
            value = 60.0
        else:
            value = _DRISHTI_VALUE.get(distance, 0.0)
        if value == 0.0:
            continue
        net += value if other in _BENEFIC_FOR_DRIK else -value
    return net / 4.0


# ── assembly ──────────────────────────────────────────────────────────


def compute_shadbala(chart: Chart, planet: str) -> Shadbala:
    """Six-fold strength for one planet, component by component."""
    rise, sset, real_times = _sunrise_sunset(chart)

    uchcha = _uchcha_bala(chart, planet)
    saptavargaja = _saptavargaja_bala(chart, planet)
    ojhayugma = _ojhayugma_bala(chart, planet)
    kendradi = _kendradi_bala(chart, planet)
    drekkana = _drekkana_bala(chart, planet)
    sthana = uchcha + saptavargaja + ojhayugma + kendradi + drekkana

    dig = _dig_bala(chart, planet)

    nathonnatha = _nathonnatha_bala(chart, planet)
    paksha = _paksha_bala(chart, planet)
    tribhaga = _tribhaga_bala(chart, planet, rise, sset)
    vara, hora = _vara_hora_bala(chart, planet, rise)
    ayana = _ayana_bala(chart, planet)
    kala = nathonnatha + paksha + tribhaga + vara + hora + ayana

    cheshta, cheshta_note = _cheshta_bala(chart, planet)
    naisargika = NAISARGIKA.get(planet, 0.0)
    drik = _drik_bala(chart, planet)

    notes = [cheshta_note]
    if not real_times:
        notes.append(
            "Sunrise and sunset could not be computed for this latitude; "
            "tribhaga and hora bala fall back to a flat 06:00/18:00 day."
        )
    if planet in ("Rahu", "Ketu"):
        notes.append(
            "Shadbala is classically defined for the seven grahas only. The "
            "figures here for a node are partial and should not be compared "
            "with the others."
        )

    return Shadbala(
        planet=planet,
        sthana=round(sthana, 2),
        dig=round(dig, 2),
        kala=round(kala, 2),
        cheshta=round(cheshta, 2),
        naisargika=round(naisargika, 2),
        drik=round(drik, 2),
        breakdown={
            "uchcha": round(uchcha, 2),
            "saptavargaja": round(saptavargaja, 2),
            "ojhayugma": round(ojhayugma, 2),
            "kendradi": round(kendradi, 2),
            "drekkana": round(drekkana, 2),
            "nathonnatha": round(nathonnatha, 2),
            "paksha": round(paksha, 2),
            "tribhaga": round(tribhaga, 2),
            "vara": round(vara, 2),
            "hora": round(hora, 2),
            "ayana": round(ayana, 2),
        },
        notes=notes,
        omitted=[
            "varsha bala (needs a Hindu luni-solar year lord)",
            "masa bala (needs a Hindu luni-solar month lord)",
            "yuddha bala (no victor is asserted for a planetary war)",
        ],
        complete=False,
    )


def all_shadbala(chart: Chart) -> dict[str, Shadbala]:
    """Shadbala for the seven grahas, strongest first."""
    results = {p: compute_shadbala(chart, p) for p in SEVEN}
    return dict(sorted(results.items(), key=lambda kv: kv[1].total_virupas, reverse=True))


def strongest(chart: Chart) -> str:
    return next(iter(all_shadbala(chart)))


def weakest(chart: Chart) -> str:
    return list(all_shadbala(chart))[-1]
