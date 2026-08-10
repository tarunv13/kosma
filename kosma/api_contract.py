"""
The wire contract between the Python engine and any frontend.

This is deliberately a *narrower* object than the grounding pack in
:mod:`kosma.grounding`. The pack exists to hand a language model everything the
engine knows; this exists to draw a screen. Keeping them separate means a
change to the visual layer never pressures the shape of the evidence layer.

Field names follow the shape the frontend was specified against — ``long``,
``speed``, ``house_index``, ``nakshatra``, ``aspects_hitting`` — so the
TypeScript interfaces and this module are the same contract written twice
rather than two things that drift.

Versioned: ``CONTRACT_VERSION`` changes whenever a field is removed or its
meaning changes, so a stale frontend can detect the mismatch rather than
silently render nonsense.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from . import ashtakavarga as av
from . import interpretations as interp
from . import nakshatras as nak
from . import numerology, placements, plainspeak
from . import shadbala as sb
from . import vargas as vg
from . import vedic_engine as ve
from .aspects import aspects_cast, house_lord, house_sign
from .dignity import all_dignities
from .evidence import HOUSE_TOPICS, build_evidence
from .grounding import AYANAMSA, HOUSE_SYSTEM
from .vargas import d9
from .yogas import detect_yogas

CONTRACT_VERSION = "1.2"


def _ledger_dict(e) -> dict:
    """One evidence entry as it crosses the wire."""
    return {
        "id": e.id,
        "house": e.house,
        "kind": e.kind,
        "statement": e.statement,
        "basis": e.basis,
        "source": e.source,
        "polarity": e.polarity,
        "disputed": e.disputed,
    }


# Two-letter abbreviations, used wherever the text must be legible at small
# sizes and in any font -- the chart grid above all. These always render.
GLYPHS: dict[str, str] = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

# The astronomical symbols, shown beside the abbreviation where there is room.
# They are carried *in addition to* GLYPHS rather than instead of them: the
# node symbols in particular are missing from many system fonts, and a chart
# cell that silently renders a tofu box for Rahu is worse than one that says
# "Ra". The interface shows the symbol with the abbreviation as its label.
SYMBOLS: dict[str, str] = {
    "Sun": "☉",
    "Moon": "☽",
    "Mars": "♂",
    "Mercury": "☿",
    "Jupiter": "♃",
    "Venus": "♀",
    "Saturn": "♄",
    "Rahu": "☊",
    "Ketu": "☋",
}

# A planet within one degree of a sign boundary sits in sandhi (the junction),
# where classical practice treats its results as unstable.
SANDHI_ORB = 1.0


def _planet_dto(chart: ve.Chart, name: str, dig: dict, strengths: dict, casts: list) -> dict:
    p = chart.planets[name]
    d = dig[name]
    strength = strengths.get(name)

    hitting = sorted({a.target_house for a in casts if a.source == name and not a.disputed})
    disputed_hitting = sorted({a.target_house for a in casts if a.source == name and a.disputed})

    return {
        "id": name.lower(),
        "name": name,
        "glyph": GLYPHS[name],
        "symbol": SYMBOLS[name],
        "long": round(p.longitude, 6),
        "speed": round(p.speed, 6),
        "degree": round(p.deg_in_sign, 6),
        "degree_dms": ve.degrees_to_dms(p.deg_in_sign),
        "sign": p.sign,
        "sign_index": p.sign_idx,
        "house_index": p.house,
        "nakshatra": p.nakshatra,
        "pada": p.pada,
        "nakshatra_lord": p.nak_lord,
        "nakshatra_deity": nak.by_longitude(p.longitude).deity,
        "retrograde": p.retrograde,
        "combust": d.combust,
        "sandhi": p.deg_in_sign < SANDHI_ORB or p.deg_in_sign > (30.0 - SANDHI_ORB),
        "dignity": d.state,
        "dignity_why": d.state_reason,
        "functional": d.functional,
        "benefic": d.benefic,
        "aspects_hitting": hitting,
        "aspects_hitting_disputed": disputed_hitting,
        "navamsa_sign": ve.SIGNS[d9(p.sign_idx, p.deg_in_sign)],
        "shadbala_rupas": strength.total_rupas if strength else None,
        "shadbala_band": strength.verdict if strength else None,
        # What this graha in this bhava means, with the strengths and
        # weaknesses modulated by the dignity it actually has here.
        "placement": placements.placement_reading(
            name,
            p.house,
            p.sign,
            d.state,
            retrograde=p.retrograde,
            combust=d.combust,
        ).as_dict(),
    }


def _house_dossier(
    chart: ve.Chart,
    house: int,
    dig: dict,
    avr: av.AshtakavargaReport,
    casts: list,
    active_lords: set[str],
) -> dict[str, Any]:
    """Everything structural about one bhava, in one object.

    This is what a reader actually wants when they click a house: what sign is
    on it, who rules it and where that ruler went, who is sitting in it, what
    is looking at it, how well supplied it is, and whether it is live right
    now. It is all computed or quoted — the module states structure and
    classical signification, and stops short of narrative.
    """
    lord = house_lord(chart, house)
    lord_p = chart.planets[lord]
    lord_d = dig[lord]
    points = avr.sarva_in_house(house)

    occupants = []
    for name in ve.VEDIC_PLANETS:
        p = chart.planets[name]
        if p.house != house:
            continue
        d = dig[name]
        occupants.append(
            {
                "name": name,
                "glyph": GLYPHS[name],
                "symbol": SYMBOLS[name],
                "degree_dms": ve.degrees_to_dms(p.deg_in_sign),
                "nakshatra": p.nakshatra,
                "pada": p.pada,
                "dignity": d.state,
                "dignity_why": d.state_reason,
                "retrograde": p.retrograde,
                "combust": d.combust,
                "benefic": d.benefic,
                "functional": d.functional,
            }
        )

    aspects_received = [
        {
            "planet": a.source,
            "rule": a.rule,
            "benefic": dig[a.source].benefic,
            "disputed": a.disputed,
        }
        for a in casts
        if a.target_house == house
    ]

    if points >= av.SAV_RICH:
        band = "well supplied"
    elif points <= av.SAV_POOR:
        band = "thinly supplied"
    else:
        band = "average"

    karaka = interp.BHAVA_KARAKA[house]
    karaka_p = chart.planets[karaka]

    live: list[str] = []
    if lord in active_lords:
        live.append(f"{lord}, the lord of this house, is running as a dasha lord")
    for occ in occupants:
        if occ["name"] in active_lords:
            live.append(f"{occ['name']}, sitting in this house, is running as a dasha lord")

    return {
        "house": house,
        "sign": house_sign(chart, house),
        "sign_index": (chart.ascendant_sign_idx + house - 1) % 12,
        "topic": HOUSE_TOPICS[house],
        "governs": interp.HOUSE_GOVERNS[house],
        "lord": lord,
        "lord_placement": {
            "in_house": lord_p.house,
            "in_sign": lord_p.sign,
            "degree_dms": ve.degrees_to_dms(lord_p.deg_in_sign),
            "nakshatra": lord_p.nakshatra,
            "dignity": lord_d.state,
            "dignity_why": lord_d.state_reason,
            "functional": lord_d.functional,
            "retrograde": lord_p.retrograde,
            "combust": lord_d.combust,
        },
        "occupants": occupants,
        "aspects_received": aspects_received,
        "sarvashtakavarga": points,
        "sarvashtakavarga_band": band,
        "karaka": karaka,
        "karaka_note": interp.BHAVA_KARAKA_NOTE[house],
        "karaka_placement": {
            "in_house": karaka_p.house,
            "in_sign": karaka_p.sign,
            "dignity": dig[karaka].state,
        },
        "currently_active": live,
    }


def _vargas(chart: ve.Chart) -> list[dict[str, Any]]:
    """All sixteen divisional charts, each ready to draw."""
    built = vg.build_all_vargas(chart)
    out: list[dict[str, Any]] = []
    for spec in vg.VARGAS:
        v = built[spec.code]
        out.append(
            {
                "code": v.code,
                "name": v.name,
                "divisions": spec.divisions,
                "read_for": v.domain,
                "note": v.note,
                "ascendant_sign": v.ascendant_sign,
                "ascendant_sign_index": v.ascendant_sign_idx,
                "positions": [
                    {
                        "name": body,
                        "glyph": GLYPHS[body],
                        "sign": pos.sign,
                        "sign_index": pos.sign_idx,
                        "house": pos.house,
                        "lord": pos.lord,
                        "vargottama": v.code != "D1"
                        and pos.sign_idx == chart.planets[body].sign_idx,
                    }
                    for body, pos in v.positions.items()
                ],
            }
        )
    return out


def _dasha_tree(chart: ve.Chart, now_jd: float, span_years: float = 30.0) -> dict[str, Any]:
    """Mahadashas over a window, each carrying its own antardashas."""
    dashas = ve.vimshottari_dasha(chart.planets["Moon"].longitude, chart.jd)
    lo = now_jd - 365.25 * 5
    hi = now_jd + 365.25 * span_years

    def status(start: float, end: float) -> str:
        if start <= now_jd < end:
            return "active"
        return "past" if end < now_jd else "upcoming"

    timeline: list[dict[str, Any]] = []
    for lord, start, end in dashas:
        if end < lo or start > hi:
            continue
        children = [
            {
                "lord": al,
                "from": ve.jd_to_date(a_start),
                "to": ve.jd_to_date(a_end),
                "from_jd": round(a_start, 4),
                "to_jd": round(a_end, 4),
                "status": status(a_start, a_end),
            }
            for _ml, al, a_start, a_end in ve.antardasha_sequence([(lord, start, end)], start, end)
        ]
        timeline.append(
            {
                "lord": lord,
                "from": ve.jd_to_date(start),
                "to": ve.jd_to_date(end),
                "from_jd": round(start, 4),
                "to_jd": round(end, 4),
                "status": status(start, end),
                "children": children,
            }
        )

    maha, antar, prat = ve.current_periods(dashas, now_jd)
    return {
        "current": {
            "mahadasha": maha[0] if maha else None,
            "antardasha": antar[0] if antar else None,
            "pratyantardasha": prat[0] if prat else None,
        },
        "timeline": timeline,
    }


def build_chart_payload(
    *,
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    tz: float,
    place: str,
    gender: str = "unspecified",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Everything a frontend needs to draw the chart, and nothing more."""
    now = now or datetime.now(UTC)
    chart = ve.build_chart(
        label=name or "Anonymous",
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lon_geo=lon,
        tz=tz,
    )
    now_jd = ve.local_to_ut(now.year, now.month, now.day, now.hour, now.minute, 0.0)

    dig = all_dignities(chart)
    strengths = sb.all_shadbala(chart)
    casts = aspects_cast(chart)
    avr = av.compute_ashtakavarga(chart)
    yreport = detect_yogas(chart)
    ev = build_evidence(chart, chart.jd, now_jd)
    panchanga = ve.panchanga_for(chart)

    dashas = ve.vimshottari_dasha(chart.planets["Moon"].longitude, chart.jd)
    maha, antar, _prat = ve.current_periods(dashas, now_jd)
    active_lords = {p[0] for p in (maha, antar) if p}

    return {
        "contract_version": CONTRACT_VERSION,
        "chart_meta": {
            "generator": "KOSMA",
            "ayanamsa": AYANAMSA,
            "ayanamsa_value": round(chart.ayanamsa, 6),
            "zodiac": "sidereal",
            "house_system": HOUSE_SYSTEM,
            "location": {"lat": lat, "lon": lon, "tz": tz, "label": place},
            "datetime": (f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"),
            "computed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "subject": name or None,
        },
        "ascendant": {
            "sign": chart.ascendant_sign,
            "sign_index": chart.ascendant_sign_idx,
            "long": round(chart.ascendant_lon, 6),
            "degree": round(chart.ascendant_deg, 6),
            "degree_dms": ve.degrees_to_dms(chart.ascendant_deg),
            "nakshatra": chart.ascendant_nak,
            "pada": chart.ascendant_pada,
            "lord": ve.LAGNA_LORDS[chart.ascendant_sign],
        },
        "planets": [_planet_dto(chart, n, dig, strengths, casts) for n in ve.VEDIC_PLANETS],
        "houses": [_house_dossier(chart, h, dig, avr, casts, active_lords) for h in range(1, 13)],
        "vargas": _vargas(chart),
        "panchanga": {
            "vara": panchanga.vara,
            "tithi": panchanga.tithi,
            "paksha": panchanga.paksha,
            "yoga": panchanga.yoga,
            "karana": panchanga.karana,
            "moon_nakshatra": panchanga.moon_nakshatra,
        },
        "yogas": [
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
        "dashas": _dasha_tree(chart, now_jd),
        "findings": [
            {
                "house": f.house,
                "topic": f.topic,
                "verdict": f.verdict,
                "confidence": f.confidence,
                "kinds": list(f.distinct_kinds),
                "citations": list(f.citations),
                # The same finding said in ordinary English. Built from the
                # ledger entries this finding already cites, so the prose and
                # the evidence can never drift apart.
                "plain": plainspeak.house_reading(
                    f.house,
                    f.topic,
                    f.verdict,
                    f.confidence,
                    [_ledger_dict(e) for e in ev.ledger if e.id in set(f.citations)],
                ).as_dict(),
            }
            for f in ev.findings
        ],
        "withheld": [
            {
                "house": w.house,
                "topic": w.topic,
                "reason": w.reason,
                "plain": plainspeak.withheld_reading(w.house, w.topic, w.reason),
            }
            for w in ev.withheld
        ],
        "evidence": [_ledger_dict(e) for e in ev.ledger],
        "gate": {
            "rule": ev.gate,
            "minimum_agreeing_kinds": ev.min_distinct_kinds,
        },
        # Plain meanings for the Sanskrit and the jargon, so a term can be
        # explained where it appears instead of on a page nobody visits.
        "glossary": plainspeak.GLOSSARY,
        "kind_labels": plainspeak.KIND_LABEL,
        # Reported beside the chart and deliberately outside the gate. See
        # kosma.numerology for why it casts no vote.
        "numerology": numerology.compute(name or "", date(year, month, day)),
        "gender": gender,
        "disclaimer": (
            "Computed in memory and not stored. For reflection; not medical, "
            "legal, financial or psychological advice."
        ),
    }


# ── Compatibility ─────────────────────────────────────────────────────


def _koota_dto(k: Any) -> dict[str, Any]:
    return {
        "name": k.name,
        "score": k.score,
        "maximum": k.maximum,
        "fraction": round(k.fraction, 4),
        "detail": k.detail,
        "rule": k.rule,
        "source": k.source,
        "void": k.void,
        "full": k.full,
        "variant_note": k.variant_note,
    }


def _pair_dto(pair: Any) -> dict[str, Any]:
    """One comparison, findings first and the score reported beneath."""
    return {
        "a": pair.a,
        "b": pair.b,
        "mode": pair.mode,
        "findings": [
            {
                "topic": t.topic,
                "description": t.description,
                "verdict": t.verdict,
                "confidence": t.confidence,
                "kinds": list(t.outcome.kinds),
                "citations": list(t.citations),
            }
            for t in pair.findings
        ],
        "withheld": [
            {
                "topic": t.topic,
                "description": t.description,
                "reason": t.outcome.failure_reason(t.topic),
            }
            for t in pair.withheld
        ],
        "milan": {
            "scheme": pair.milan.scheme,
            "total": pair.milan.total,
            "maximum": pair.milan.maximum,
            "percentage": pair.milan.percentage,
            "critique": pair.milan.critique,
            "kootas": [_koota_dto(k) for k in pair.milan.kootas],
        },
        "doshas": [
            {
                "name": d.name,
                "present": d.present,
                "cancelled": d.cancelled,
                "status": d.status,
                "detail": d.detail,
                "cancellations": list(d.cancellations),
                "source": d.source,
                "note": d.note,
            }
            for d in pair.doshas
        ],
        "overlays": {
            "a_into_b": [
                {
                    "planet": o.planet,
                    "house": o.into_house,
                    "theme": o.theme,
                    "polarity": o.polarity,
                }
                for o in pair.overlays_ab
            ],
            "b_into_a": [
                {
                    "planet": o.planet,
                    "house": o.into_house,
                    "theme": o.theme,
                    "polarity": o.polarity,
                }
                for o in pair.overlays_ba
            ],
        },
        "cross_aspects": [
            {
                "from_person": c.source_owner,
                "planet": c.source_planet,
                "to_person": c.target_owner,
                "target": c.target,
                "rule": c.rule,
                "polarity": c.polarity,
            }
            for c in pair.cross_ab + pair.cross_ba
        ],
        "dasha_sync": {
            "a_mahadasha": pair.sync.a_maha,
            "a_antardasha": pair.sync.a_antar,
            "b_mahadasha": pair.sync.b_maha,
            "b_antardasha": pair.sync.b_antar,
            "relation": pair.sync.relation,
            "shared": list(pair.sync.shared),
            "detail": pair.sync.detail,
        },
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
            for e in pair.ledger
        ],
        "navamsa_note": pair.navamsa_note,
    }


def build_compatibility_payload(
    people: list[dict[str, Any]],
    *,
    mode: str = "relationship",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Pairwise comparison across two or more charts.

    Pairwise deliberately: there is no classical method for scoring a group as
    a whole, and averaging the pairs into one number would be inventing one.
    """
    from . import compatibility as cp

    now = now or datetime.now(UTC)
    now_jd = ve.local_to_ut(now.year, now.month, now.day, now.hour, now.minute, 0.0)

    built: list[cp.Person] = []
    profiles: list[dict[str, Any]] = []
    for person in people:
        chart = ve.build_chart(
            label=person["label"],
            year=person["year"],
            month=person["month"],
            day=person["day"],
            hour=person["hour"],
            minute=person["minute"],
            lat=person["lat"],
            lon_geo=person["lon"],
            tz=person["tz"],
        )
        built.append(cp.Person(label=person["label"], chart=chart))
        moon = chart.planets["Moon"]
        profiles.append(
            {
                "label": person["label"],
                "place": person["place"],
                "datetime": (
                    f"{person['year']:04d}-{person['month']:02d}-{person['day']:02d}"
                    f"T{person['hour']:02d}:{person['minute']:02d}"
                ),
                "ascendant": chart.ascendant_sign,
                "ascendant_dms": ve.degrees_to_dms(chart.ascendant_deg),
                "moon_sign": moon.sign,
                "moon_nakshatra": moon.nakshatra,
                "moon_pada": moon.pada,
            }
        )

    pairs = (
        [cp.compare(built[0], built[1], now_jd, mode)]
        if len(built) == 2
        else cp.compare_group(built, now_jd, mode).pairs
    )

    return {
        "contract_version": CONTRACT_VERSION,
        "mode": mode,
        "computed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "people": profiles,
        "pairs": [_pair_dto(p) for p in pairs],
        "gate": {
            "minimum_agreeing_kinds": 2,
            "factor_kinds": list(cp.COMPAT_FACTOR_KINDS),
        },
        "disclaimer": (
            "A dosha is a flag to examine, not a disqualification of a person. "
            "Varna is a classification by the Moon sign's element, not anyone's "
            "birth caste."
        ),
    }
