"""
The grounding pack: everything the engine computed, as one JSON object.

This is the handoff between the two halves of the system. The ephemeris
computes; the language model interprets. Neither does the other's job.

A model handed this pack is not being asked to remember astrology. Every
degree, dignity, yoga, dasha date, transit window and piece of evidence is
already resolved, cited, and either cleared or withheld by the confirmation
gate. The model's whole remaining task is to render what survived into
language a person can use.

The accompanying system prompt binds the model to the pack: it may not
calculate, may not add a yoga, and may not discuss any topic the gate
withheld.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from . import ashtakavarga as av
from . import kp as kp_mod
from . import nakshatras as nak
from . import shadbala as sb
from . import transits as tr
from . import vargas as vg
from . import vedic_engine as ve
from .aspects import all_chains, conjunctions, house_lord, house_sign, mutual_aspects
from .dignity import all_dignities
from .evidence import FACTOR_KINDS, MIN_DISTINCT_KINDS, build_evidence
from .yogas import detect_yogas

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"

AYANAMSA = "Lahiri (Chitrapaksha)"
HOUSE_SYSTEM = "whole-sign from the natal lagna, with Placidus cusps retained for KP"


@dataclass(frozen=True)
class BirthInput:
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    lat: float
    lon: float
    tz: float
    place: str

    @property
    def iso(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}T{self.hour:02d}:{self.minute:02d}"


def _planet_block(chart: ve.Chart, dig: dict, strengths: dict, name: str) -> dict[str, Any]:
    p = chart.planets[name]
    d = dig[name]
    s = strengths.get(name)
    block: dict[str, Any] = {
        "name": name,
        "sign": p.sign,
        "degree_in_sign": round(p.deg_in_sign, 6),
        "degree_dms": ve.degrees_to_dms(p.deg_in_sign),
        "absolute_longitude": round(p.longitude, 6),
        "house_whole_sign": p.house,
        "house_placidus": kp_mod.kp_house_of(chart, p.longitude),
        "retrograde": p.retrograde,
        "daily_speed": round(p.speed, 6),
        "nakshatra": nak.describe(p.longitude),
        "kp_chain": {
            "star_lord": p.star_lord,
            "sub_lord": p.sub_lord,
            "sub_sub_lord": p.sub_sub_lord,
        },
        "dignity": {
            "state": d.state,
            "why": d.state_reason,
            "natural_benefic": d.benefic,
            "natural_benefic_why": d.benefic_reason,
            "functional_nature": d.functional,
            "functional_why": d.functional_reason,
            "houses_ruled": d.houses_ruled,
            "combust": d.combust,
            "combust_detail": d.combust_note,
            "directional_strength": d.dig_bala,
            "planetary_war_with": d.planetary_war_with,
            "deep_note": d.deep_note,
            "disputed": d.disputed,
        },
        "varga_consistency": vg.varga_dignity_count(chart, name),
    }
    if s is not None:
        block["shadbala"] = {
            "total_rupas": s.total_rupas,
            "required_rupas": s.required_rupas,
            "ratio": s.ratio,
            "band": s.verdict,
            "components": {
                "sthana": s.sthana,
                "dig": s.dig,
                "kala": s.kala,
                "cheshta": s.cheshta,
                "naisargika": s.naisargika,
                "drik": s.drik,
            },
            "breakdown": s.breakdown,
            "notes": s.notes,
            "omitted_components": s.omitted,
            "complete": s.complete,
        }
    return block


def build_pack(
    birth: BirthInput,
    *,
    now: datetime | None = None,
    varga_codes: tuple[str, ...] = vg.SHODASAVARGA,
    activation_years: float = 8.0,
) -> dict[str, Any]:
    """Compute everything and return it as one serialisable dictionary."""
    now = now or datetime.now(UTC)

    chart = ve.build_chart(
        label=birth.name or "Anonymous",
        year=birth.year,
        month=birth.month,
        day=birth.day,
        hour=birth.hour,
        minute=birth.minute,
        lat=birth.lat,
        lon_geo=birth.lon,
        tz=birth.tz,
    )
    birth_jd = chart.jd
    now_jd = ve.local_to_ut(now.year, now.month, now.day, now.hour, now.minute, 0.0)

    dig = all_dignities(chart)
    strengths = sb.all_shadbala(chart)
    yreport = detect_yogas(chart)
    avreport = av.compute_ashtakavarga(chart)
    panchanga = ve.panchanga_for(chart)
    karakas = ve.jaimini_karakas(chart)
    dashas = ve.vimshottari_dasha(chart.planets["Moon"].longitude, birth_jd)
    maha, antar, prat = ve.current_periods(dashas, now_jd)
    snapshot = tr.transit_snapshot(chart, now_jd)
    ss = tr.sade_sati(chart, now_jd)
    windows = tr.activation_windows(chart, birth_jd, now_jd, now_jd + activation_years * 365.25)
    ev = build_evidence(chart, birth_jd, now_jd)
    chains = all_chains(chart)

    return {
        "meta": {
            "generator": f"KOSMA {__version__}",
            "computed_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ephemeris": "Swiss Ephemeris (pyswisseph)",
            "ayanamsa": AYANAMSA,
            "ayanamsa_value_deg": round(chart.ayanamsa, 6),
            "zodiac": "sidereal",
            "house_system": HOUSE_SYSTEM,
            "node": "mean lunar node (Rahu), Ketu derived at exactly 180 degrees",
            "tradition": "Vedic (Parashari, Jaimini, KP). No Western/tropical "
            "calculation is mixed in anywhere in this pack.",
            "contract": (
                "Every number in this pack is computed. The reader of this pack "
                "must not recalculate, estimate, or supplement any of it."
            ),
        },
        "birth": {
            "name": birth.name or None,
            "local_datetime": birth.iso,
            "timezone_offset_hours": birth.tz,
            "place": birth.place,
            "latitude": birth.lat,
            "longitude": birth.lon,
            "julian_day_ut": round(birth_jd, 8),
            "storage_note": (
                "Computed in memory for this response only. Not written to disk, "
                "not logged, not retained server-side."
            ),
            "accuracy_note": (
                "The ascendant moves about one degree every four minutes. A birth "
                "time uncertain by ten minutes can change the lagna nakshatra pada "
                "and several KP sub-divisions, which would change parts of this "
                "pack. Treat a rounded or remembered birth time as provisional."
            ),
        },
        "ascendant": {
            "sign": chart.ascendant_sign,
            "degree_in_sign": round(chart.ascendant_deg, 6),
            "degree_dms": ve.degrees_to_dms(chart.ascendant_deg),
            "absolute_longitude": round(chart.ascendant_lon, 6),
            "nakshatra": nak.describe(chart.ascendant_lon),
            "kp_chain": {
                "star_lord": chart.ascendant_kp[0],
                "sub_lord": chart.ascendant_kp[1],
                "sub_sub_lord": chart.ascendant_kp[2],
            },
            "lagna_lord": ve.LAGNA_LORDS[chart.ascendant_sign],
        },
        "houses": [
            {
                "house": h,
                "sign": house_sign(chart, h),
                "lord": house_lord(chart, h),
                "lord_sits_in_house": chart.planets[house_lord(chart, h)].house,
                "occupants": [n for n in ve.VEDIC_PLANETS if chart.planets[n].house == h],
                "sarvashtakavarga_points": avreport.sarva_in_house(h),
            }
            for h in range(1, 13)
        ],
        "planets": [_planet_block(chart, dig, strengths, n) for n in ve.VEDIC_PLANETS],
        "conjunctions": [
            {
                "planets": list(c.planets),
                "sign": c.sign,
                "house": c.house,
                "spread_degrees": c.max_separation,
                "tight": c.close,
            }
            for c in conjunctions(chart)
        ],
        "mutual_aspects": [
            {"between": [a, b], "rule": rule} for a, b, rule in mutual_aspects(chart)
        ],
        "chains": {
            name: {
                "dispositor": {
                    "path": list(v["dispositor"].path),
                    "terminus": v["dispositor"].terminus,
                    "note": v["dispositor"].note,
                },
                "nakshatra": {
                    "path": list(v["nakshatra"].path),
                    "terminus": v["nakshatra"].terminus,
                    "note": v["nakshatra"].note,
                },
            }
            for name, v in chains.items()
        },
        "panchanga": {
            "vara": panchanga.vara,
            "tithi": panchanga.tithi,
            "paksha": panchanga.paksha,
            "yoga": panchanga.yoga,
            "karana": panchanga.karana,
            "moon_nakshatra": panchanga.moon_nakshatra,
            "moon_pada": panchanga.moon_pada,
            "sun_moon_arc_degrees": round(panchanga.sun_moon_diff, 4),
        },
        "jaimini_karakas": karakas,
        "vargas": {
            code: {
                "name": v.name,
                "read_for": v.domain,
                "ascendant_sign": v.ascendant_sign,
                "positions": {
                    b: {"sign": pos.sign, "house": pos.house, "lord": pos.lord}
                    for b, pos in v.positions.items()
                },
                "note": v.note,
            }
            for code, v in vg.build_all_vargas(chart, varga_codes).items()
        },
        "ashtakavarga": {
            "bhinna": {
                p: {
                    "by_sign": list(b.points_by_sign),
                    "total": b.total,
                }
                for p, b in avreport.bhinna.items()
            },
            "sarva_by_sign": list(avreport.sarva_by_sign),
            "sarva_by_house": avreport.sarva_by_house(),
            "sarva_total": avreport.sarva_total,
            "strong_houses": avreport.strong_houses(),
            "weak_houses": avreport.weak_houses(),
            "thresholds": {"strong_at_or_above": av.SAV_RICH, "weak_at_or_below": av.SAV_POOR},
        },
        "kp": kp_mod.kp_summary(chart),
        "yogas": {
            "formed": [
                {
                    "name": y.name,
                    "planets": list(y.planets),
                    "houses": list(y.houses),
                    "detail": y.detail,
                    "rule": y.rule,
                    "source": y.source,
                    "polarity": y.polarity,
                    "caveat": y.caveat,
                    "disputed": y.disputed,
                }
                for y in yreport.formed
            ],
            "note": (
                "This list is exhaustive for the rule set this engine implements. "
                "If a yoga is not listed, it was not formed. Do not add one."
            ),
        },
        "dasha": {
            "system": "Vimshottari, 120-year cycle anchored to the natal Moon's nakshatra",
            "current": {
                "mahadasha": _period(maha),
                "antardasha": _period(antar),
                "pratyantardasha": _period(prat),
            },
            "timeline": [
                {
                    "lord": lord,
                    "from": ve.jd_to_date(start),
                    "to": ve.jd_to_date(end),
                    "status": (
                        "active"
                        if start <= now_jd < end
                        else ("past" if end < now_jd else "upcoming")
                    ),
                }
                for lord, start, end in dashas
                if end > now_jd - 365.25 * 10 and start < now_jd + 365.25 * 40
            ],
        },
        "transits": {
            "as_of_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "positions": {
                p: {
                    "sign": t.sign,
                    "degree": t.degree,
                    "house_from_lagna": t.house_from_lagna,
                    "house_from_moon": t.house_from_moon,
                    "retrograde": t.retrograde,
                    "classical_condition": t.condition,
                }
                for p, t in snapshot.items()
            },
            "sade_sati": {
                "active": ss.active,
                "phase": ss.phase,
                "window": ss.window,
                "note": ss.note,
            },
        },
        "activation_windows": {
            "method": (
                "Interval intersection between an antardasha and a slow-mover "
                "transit through a sign owned or natally occupied by the "
                "mahadasha or antardasha lord, or the natal lagna or Moon sign. "
                "Dates come from bisected ephemeris ingresses, not estimates."
            ),
            "horizon_years": activation_years,
            "windows": [
                {
                    "from": ve.jd_to_date(w.start_jd),
                    "to": ve.jd_to_date(w.end_jd),
                    "days": w.days,
                    "mahadasha": w.mahadasha,
                    "antardasha": w.antardasha,
                    "transiting": w.transiting,
                    "transit_sign": w.transit_sign,
                    "triggers": list(w.triggers),
                    "converging_factors": w.factor_count,
                }
                for w in windows
            ],
            "caveat": (
                "These are windows of activation, not events. Classical practice "
                "distinguishes the promise of a chart from the timing of its "
                "delivery: a window says a theme is live, never that a specific "
                "thing will happen."
            ),
        },
        "evidence": {
            "gate": ev.gate,
            "minimum_agreeing_kinds": MIN_DISTINCT_KINDS,
            "factor_kinds": list(FACTOR_KINDS),
            "findings": [
                {
                    "house": f.house,
                    "topic": f.topic,
                    "verdict": f.verdict,
                    "confidence": f.confidence,
                    "agreeing_kinds": list(f.distinct_kinds),
                    "net_polarity": f.net_polarity,
                    "citations": list(f.citations),
                    "evidence": [
                        {
                            "id": e.id,
                            "kind": e.kind,
                            "statement": e.statement,
                            "basis": e.basis,
                            "source": e.source,
                            "polarity": e.polarity,
                            "disputed": e.disputed,
                        }
                        for e in f.evidence
                    ],
                }
                for f in ev.findings
            ],
            "withheld": [
                {
                    "house": w.house,
                    "topic": w.topic,
                    "reason": w.reason,
                    "kinds_found": list(w.kinds_found),
                }
                for w in ev.withheld
            ],
        },
        "constraints": CONSTRAINTS,
    }


def _period(period: tuple | None) -> dict[str, Any] | None:
    if not period:
        return None
    lord, start, end = period
    return {"lord": lord, "from": ve.jd_to_date(start), "to": ve.jd_to_date(end)}


CONSTRAINTS: list[str] = [
    "Do not calculate. Every position, dignity, dasha date and transit window "
    "you need is already in this pack. If a number is not here, say it is not "
    "available rather than deriving it.",
    "Do not introduce a yoga, rule, or combination that is not in the yogas "
    "list. If it is not listed, it was not formed in this chart.",
    "Do not discuss any house listed under evidence.withheld. The chart does "
    "not support a reading of it. Say so plainly if asked.",
    "Cite the evidence ids you are relying on, so a practitioner can check "
    "your reasoning against the chart.",
    "Treat anything marked disputed as disputed. Name the disagreement rather "
    "than picking a side silently.",
    "Distinguish the promise of the chart from the timing of events. An "
    "activation window marks a live theme, not a scheduled occurrence.",
    "Do not give medical, legal, financial, or psychiatric advice, and do not "
    "predict death, terminal illness, or the outcome of a pregnancy.",
]


def to_json(pack: dict[str, Any], *, indent: int | None = 2) -> str:
    return json.dumps(pack, indent=indent, ensure_ascii=False, default=str)


def system_prompt() -> str:
    """The interpretation-layer system prompt shipped with the repo."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return _FALLBACK_PROMPT


_FALLBACK_PROMPT = (
    "You are a Vedic Jyotish acharya interpreting a chart that has already "
    "been computed for you. You do not calculate. You may only interpret what "
    "the accompanying grounding pack contains, you must respect its "
    "constraints list, and you must not discuss any topic it marks withheld."
)


def bundle(pack: dict[str, Any]) -> str:
    """Prompt plus pack, ready to paste into any model or Project."""
    return (
        f"{system_prompt()}\n\n"
        "---\n\n"
        "## GROUNDING PACK (authoritative; do not recompute)\n\n"
        "```json\n"
        f"{to_json(pack)}\n"
        "```\n"
    )
