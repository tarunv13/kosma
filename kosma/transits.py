"""
Gochara (transits) and dasha-transit activation windows.

Event timing is the thing practising astrologers most consistently report that
language models get wrong, and it is also the thing that is most mechanically
derivable. Nothing here is estimated: sign ingress dates are found by scanning
the ephemeris and bisecting to the minute, and activation windows are literal
interval intersections between a dasha period and a transit span.

Sources
-------
* Brihat Parashara Hora Shastra ch. 47-48 — gochara from the Moon.
* Phaladeepika ch. 26 — transit results reckoned from the janma rashi.
* Standard vimshottari proportional rule for antardasha lengths.
"""

from __future__ import annotations

from dataclasses import dataclass

import swisseph as swe

from .dignity import OWN_SIGNS
from .vedic_engine import (
    PLANETS,
    SIGNS,
    Chart,
    antardasha_sequence,
    get_planet_lon,
    jd_to_date,
    vimshottari_dasha,
)

SLOW_MOVERS = ("Saturn", "Jupiter", "Rahu", "Ketu")

# Classical gochara conditions named from the natal Moon sign.
SATURN_FROM_MOON: dict[int, str] = {
    12: "Sade Sati, rising phase (Saturn in the 12th from the natal Moon)",
    1: "Sade Sati, peak phase (Saturn over the natal Moon)",
    2: "Sade Sati, setting phase (Saturn in the 2nd from the natal Moon)",
    4: "Ardhashtama Shani (Saturn in the 4th from the natal Moon)",
    8: "Ashtama Shani (Saturn in the 8th from the natal Moon)",
}

JUPITER_FROM_MOON_FAVOURABLE = (2, 5, 7, 9, 11)


def _lon_at(jd: float, planet: str) -> float:
    """Sidereal longitude of a body at a Julian Day."""
    if planet == "Ketu":
        lon, _ = get_planet_lon(jd, swe.MEAN_NODE)
        return (lon + 180.0) % 360.0
    pid = PLANETS[planet]
    if pid is None:  # pragma: no cover - only Ketu has a None id
        raise ValueError(f"no ephemeris id for {planet}")
    lon, _ = get_planet_lon(jd, pid)
    return lon % 360.0


def _sign_at(jd: float, planet: str) -> int:
    return int(_lon_at(jd, planet) // 30)


# ── ingress scanning ──────────────────────────────────────────────────


@dataclass(frozen=True)
class Ingress:
    planet: str
    jd: float
    from_sign: str
    to_sign: str
    retrograde_entry: bool

    @property
    def date(self) -> str:
        return jd_to_date(self.jd)


def sign_ingresses(
    planet: str, start_jd: float, end_jd: float, step_days: float = 5.0
) -> list[Ingress]:
    """Every sign change of ``planet`` in a window, bisected to the minute.

    Only meaningful for slow movers; a five-day step would skip signs for the
    Moon or Mercury.
    """
    out: list[Ingress] = []
    jd = start_jd
    prev = _sign_at(jd, planet)
    while jd < end_jd:
        nxt = min(jd + step_days, end_jd)
        current = _sign_at(nxt, planet)
        if current != prev:
            lo, hi = jd, nxt
            for _ in range(40):  # ~1e-9 day, far finer than needed
                mid = (lo + hi) / 2.0
                if _sign_at(mid, planet) == prev:
                    lo = mid
                else:
                    hi = mid
            out.append(
                Ingress(
                    planet=planet,
                    jd=hi,
                    from_sign=SIGNS[prev],
                    to_sign=SIGNS[current],
                    retrograde_entry=((current - prev) % 12) > 6,
                )
            )
            prev = current
        jd = nxt
    return out


@dataclass(frozen=True)
class SignSpan:
    planet: str
    sign_idx: int
    sign: str
    start_jd: float
    end_jd: float

    def overlaps(self, a: float, b: float) -> tuple[float, float] | None:
        lo, hi = max(self.start_jd, a), min(self.end_jd, b)
        return (lo, hi) if lo < hi else None


def sign_spans(planet: str, start_jd: float, end_jd: float) -> list[SignSpan]:
    """Contiguous intervals during which ``planet`` holds one sign."""
    ingresses = sign_ingresses(planet, start_jd, end_jd)
    spans: list[SignSpan] = []
    cursor = start_jd
    sign = _sign_at(start_jd, planet)
    for ing in ingresses:
        spans.append(
            SignSpan(
                planet=planet,
                sign_idx=sign,
                sign=SIGNS[sign],
                start_jd=cursor,
                end_jd=ing.jd,
            )
        )
        cursor = ing.jd
        sign = SIGNS.index(ing.to_sign)
    spans.append(
        SignSpan(planet=planet, sign_idx=sign, sign=SIGNS[sign], start_jd=cursor, end_jd=end_jd)
    )
    return spans


# ── snapshot ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TransitPosition:
    planet: str
    sign: str
    degree: float
    house_from_lagna: int
    house_from_moon: int
    retrograde: bool
    condition: str | None


def transit_snapshot(natal: Chart, when_jd: float) -> dict[str, TransitPosition]:
    """Where each slow mover stands relative to the natal lagna and Moon."""
    moon_sign = natal.planets["Moon"].sign_idx
    out: dict[str, TransitPosition] = {}
    for planet in SLOW_MOVERS:
        lon = _lon_at(when_jd, planet)
        sidx = int(lon // 30)
        from_lagna = ((sidx - natal.ascendant_sign_idx) % 12) + 1
        from_moon = ((sidx - moon_sign) % 12) + 1

        condition: str | None = None
        if planet == "Saturn":
            condition = SATURN_FROM_MOON.get(from_moon)
        elif planet == "Jupiter":
            condition = (
                f"Jupiter in the {_ord(from_moon)} from the natal Moon, one of the "
                "positions Phaladeepika counts as favourable"
                if from_moon in JUPITER_FROM_MOON_FAVOURABLE
                else None
            )

        retro = planet in ("Rahu", "Ketu")
        if not retro:
            pid = PLANETS[planet]
            if pid is not None:
                _, speed = get_planet_lon(when_jd, pid)
                retro = speed < 0

        out[planet] = TransitPosition(
            planet=planet,
            sign=SIGNS[sidx],
            degree=round(lon - sidx * 30.0, 4),
            house_from_lagna=from_lagna,
            house_from_moon=from_moon,
            retrograde=retro,
            condition=condition,
        )
    return out


@dataclass(frozen=True)
class SadeSati:
    active: bool
    phase: str | None
    start_jd: float | None
    end_jd: float | None
    note: str

    @property
    def window(self) -> str | None:
        if self.start_jd is None or self.end_jd is None:
            return None
        return f"{jd_to_date(self.start_jd)} to {jd_to_date(self.end_jd)}"


def sade_sati(natal: Chart, today_jd: float, horizon_years: float = 40.0) -> SadeSati:
    """Saturn's seven-and-a-half-year passage over the natal Moon.

    The window is found from actual Saturn ingresses, so retrograde re-entries
    into the 12th or 2nd are reflected in the dates rather than assumed away.
    """
    moon_sign = natal.planets["Moon"].sign_idx
    phases = {(moon_sign + 11) % 12, moon_sign, (moon_sign + 1) % 12}

    start = today_jd - horizon_years * 365.25 / 2
    end = today_jd + horizon_years * 365.25 / 2
    spans = [s for s in sign_spans("Saturn", start, end) if s.sign_idx in phases]

    current = next((s for s in spans if s.start_jd <= today_jd < s.end_jd), None)
    if current is None:
        upcoming = [s for s in spans if s.start_jd > today_jd]
        if upcoming:
            nxt = min(upcoming, key=lambda s: s.start_jd)
            return SadeSati(
                active=False,
                phase=None,
                start_jd=nxt.start_jd,
                end_jd=None,
                note=(
                    f"Not running. Saturn next enters the 12th from the natal Moon "
                    f"around {jd_to_date(nxt.start_jd)}."
                ),
            )
        return SadeSati(
            active=False,
            phase=None,
            start_jd=None,
            end_jd=None,
            note="Not running within the scanned window.",
        )

    # Merge contiguous qualifying spans into one continuous passage.
    ordered = sorted(spans, key=lambda s: s.start_jd)
    idx = ordered.index(current)
    lo = idx
    while lo > 0 and abs(ordered[lo - 1].end_jd - ordered[lo].start_jd) < 1.0:
        lo -= 1
    hi = idx
    while hi + 1 < len(ordered) and abs(ordered[hi].end_jd - ordered[hi + 1].start_jd) < 1.0:
        hi += 1

    from_moon = ((current.sign_idx - moon_sign) % 12) + 1
    return SadeSati(
        active=True,
        phase=SATURN_FROM_MOON.get(from_moon, f"Saturn in the {_ord(from_moon)} from the Moon"),
        start_jd=ordered[lo].start_jd,
        end_jd=ordered[hi].end_jd,
        note=(
            f"Saturn currently transits {current.sign}, the {_ord(from_moon)} from "
            f"the natal Moon in {SIGNS[moon_sign]}."
        ),
    )


# ── dasha x transit activation ────────────────────────────────────────


@dataclass(frozen=True)
class ActivationWindow:
    """An interval where a dasha lord is also being triggered by transit."""

    start_jd: float
    end_jd: float
    mahadasha: str
    antardasha: str
    transiting: str
    transit_sign: str
    triggers: tuple[str, ...]
    factor_count: int

    @property
    def window(self) -> str:
        return f"{jd_to_date(self.start_jd)} to {jd_to_date(self.end_jd)}"

    @property
    def days(self) -> float:
        return round(self.end_jd - self.start_jd, 1)


def activation_windows(
    natal: Chart,
    birth_jd: float,
    from_jd: float,
    to_jd: float,
    min_days: float = 30.0,
) -> list[ActivationWindow]:
    """Periods where a running dasha lord is simultaneously hit by transit.

    A window is emitted only when a slow-moving transit occupies a sign that
    the mahadasha or antardasha lord owns or natally occupies, or the natal
    lagna or Moon sign, during that antardasha. The overlap is a literal
    interval intersection, and short overlaps are dropped so the output stays
    readable rather than exhaustive.
    """
    dashas = vimshottari_dasha(natal.planets["Moon"].longitude, birth_jd)
    periods = antardasha_sequence(dashas, from_jd, to_jd)
    if not periods:
        return []

    spans_by_planet = {p: sign_spans(p, from_jd, to_jd) for p in SLOW_MOVERS}

    lagna_sign = SIGNS[natal.ascendant_sign_idx]
    moon_sign = natal.planets["Moon"].sign

    out: list[ActivationWindow] = []
    for maha, antar, a_start, a_end in periods:
        lords = {maha, antar}
        natal_signs = {natal.planets[p].sign for p in lords if p in natal.planets}
        owned: set[str] = set()
        for p in lords:
            owned.update(OWN_SIGNS.get(p, []))

        for transiting, spans in spans_by_planet.items():
            for span in spans:
                triggers: list[str] = []
                if span.sign in natal_signs:
                    who = [p for p in sorted(lords) if natal.planets[p].sign == span.sign]
                    triggers.append(
                        f"{transiting} transits {span.sign}, the natal sign of {' and '.join(who)}"
                    )
                if span.sign in owned:
                    who = [p for p in sorted(lords) if span.sign in OWN_SIGNS.get(p, [])]
                    triggers.append(
                        f"{transiting} transits {span.sign}, owned by {' and '.join(who)}"
                    )
                if span.sign == lagna_sign:
                    triggers.append(f"{transiting} transits the natal lagna sign {span.sign}")
                if span.sign == moon_sign:
                    triggers.append(f"{transiting} transits the natal Moon sign {span.sign}")
                if not triggers:
                    continue

                overlap = span.overlaps(max(a_start, from_jd), min(a_end, to_jd))
                if overlap is None or (overlap[1] - overlap[0]) < min_days:
                    continue

                out.append(
                    ActivationWindow(
                        start_jd=overlap[0],
                        end_jd=overlap[1],
                        mahadasha=maha,
                        antardasha=antar,
                        transiting=transiting,
                        transit_sign=span.sign,
                        triggers=tuple(triggers),
                        factor_count=len(triggers) + 1,  # +1 for the dasha itself
                    )
                )

    out.sort(key=lambda w: (w.start_jd, -w.factor_count))
    return out


def _ord(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"
