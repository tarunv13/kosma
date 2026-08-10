"""Plain-language narration of what the gate has already established.

The engine's output is precise and completely opaque to anyone who has not
read Parashara. A finding arrives as `house 2 / contested / well corroborated
/ [house_lord_placement, aspect, nakshatra_lord, yoga, dignity,
ashtakavarga]`, which is an accurate description of a decision procedure and
tells a reader nothing about their life.

This module writes the sentence that was missing. Three rules govern it:

* **It narrates; it never concludes.** Every sentence here is a restatement of
  evidence the gate already accepted, in ordinary words. Nothing is added, no
  claim is strengthened, and a withheld area stays withheld -- the plain voice
  is not a back door through which ungated material reaches the reader.

* **It counts what the gate counted.** Disputed evidence is excluded here for
  the same reason it is excluded there, so the prose and the ledger can never
  disagree about how many factors were in play.

* **It says what it does not know.** Each reading ends by naming its own
  limit, because a confident sentence about a thinly supported house is the
  precise failure this project exists to avoid.

The Sanskrit is kept and glossed rather than removed. A reader who wants
`ashtakavarga` should find it, and a reader who does not should not have to
look it up to learn whether their second house is well supplied.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .interpretations import BHAVA_KARAKA, HOUSE_GOVERNS

# ── Glossary ──────────────────────────────────────────────────────────
#
# Every technical term the interface can show a reader, with a one-line
# meaning. Surfaced next to the term rather than on a separate page: a
# glossary someone has to navigate to is a glossary nobody reads.

GLOSSARY: dict[str, str] = {
    "ashtakavarga": (
        "A points system. Each planet awards a point to the signs it treats "
        "well from where it sits; the totals show which parts of the chart "
        "are generously supplied and which are thin."
    ),
    "sarvashtakavarga": (
        "The combined ashtakavarga total for a house, out of 337 spread "
        "across all twelve. Above 30 is well supplied, 25 or under is thin."
    ),
    "bhava": "A house — one of the twelve divisions of life the chart is read through.",
    "dasha": (
        "A period of life assigned to a planet. The Vimshottari cycle runs "
        "120 years and hands the chart to each planet in turn."
    ),
    "mahadasha": "The major period, from six to twenty years depending on the planet.",
    "antardasha": "A sub-period inside a mahadasha, run by a second planet.",
    "dignity": (
        "How comfortable a planet is where it sits — at home in its own sign, "
        "exalted at its best, debilitated at its worst, or somewhere between."
    ),
    "exalted": "A planet at its strongest possible placement.",
    "debilitated": "A planet at its weakest placement — the sign opposite its exaltation.",
    "swakshetra": "A planet sitting in a sign it rules — at home, and steady.",
    "moolatrikona": "A planet's best working position, just short of exaltation.",
    "drishti": (
        "Aspect — the way a planet influences a house it is not sitting in. "
        "Every planet looks at the house opposite; some have additional reach."
    ),
    "graha": "A planet, in the Jyotish sense — the nine include the lunar nodes.",
    "rasi": "A sign of the zodiac, and the name of the main birth chart (D1).",
    "lagna": "The ascendant — the sign rising at the eastern horizon at birth.",
    "nakshatra": (
        "One of 27 lunar mansions. Finer than a sign, and each has a ruling "
        "planet that carries influence to wherever that planet sits."
    ),
    "kendra": "The angular houses (1, 4, 7, 10) — the load-bearing parts of a chart.",
    "trikona": "The trines (1, 5, 9) — traditionally the most fortunate houses.",
    "dusthana": "Houses 6, 8 and 12 — the difficult ones, tied to loss and crisis.",
    "yoga": "A named combination of placements the classical texts single out.",
    "vimshottari": "The 120-year dasha cycle used here, and the most widely used one.",
    "gochara": "Transits — where the planets are now, as against where they were at birth.",
    "varga": "A divisional chart, derived from the birth chart to examine one area closely.",
    "vargottama": "A planet in the same sign in a divisional chart as in the birth chart — reinforced.",
    "retrograde": "A planet appearing to move backwards from Earth. Its themes turn inward.",
    "combust": "A planet too close to the Sun to be seen, and traditionally weakened by it.",
    "karaka": "The natural significator of a matter, regardless of which house it occupies.",
    "shadbala": "A six-fold strength calculation, scoring each planet on positional and temporal grounds.",
}

# ── How each kind of factor reads in ordinary words ───────────────────
#
# Keyed by (kind, supporting?). Written to slot into "This house is ...".
# Deliberately plain: these are the sentences a reader meets first.

_KIND_PLAIN: dict[str, tuple[str, str]] = {
    "house_lord_placement": (
        "the planet that rules this part of the chart is well placed",
        "the planet that rules this part of the chart sits somewhere difficult",
    ),
    "dignity": (
        "a planet sitting here is comfortable where it is",
        "a planet sitting here is uncomfortable where it is",
    ),
    "conjunction": (
        "helpful planets sit together here",
        "planets that sit together here work against each other",
    ),
    "aspect": (
        "a benefic planet has this house in view",
        "a difficult planet has this house in view",
    ),
    "nakshatra_lord": (
        "the finer lunar placement points somewhere constructive",
        "the finer lunar placement points somewhere strained",
    ),
    "yoga": (
        "a named combination the classical texts single out touches this house",
        "a named combination the classical texts warn about touches this house",
    ),
    "dasha": (
        "the period now running favours this area",
        "the period now running presses on this area",
    ),
    "transit": (
        "the planets currently overhead support this area",
        "the planets currently overhead trouble this area",
    ),
    "ashtakavarga": (
        "the house is generously supplied with points",
        "the house is thinly supplied with points",
    ),
}

# The plain name of each factor kind, for the technical ledger's labels.
KIND_LABEL: dict[str, str] = {
    "house_lord_placement": "where the ruling planet went",
    "dignity": "how comfortable the planets here are",
    "conjunction": "planets sitting together",
    "aspect": "planets looking at this house",
    "nakshatra_lord": "the lunar-mansion chain",
    "yoga": "a named classical combination",
    "dasha": "the period now running",
    "transit": "where the planets are now",
    "ashtakavarga": "the house's point score",
}

_CONFIDENCE_PLAIN: dict[str, str] = {
    "indicative": (
        "Two kinds of factor agree here, which is the minimum this engine "
        "will report on. Treat it as a direction, not a conclusion."
    ),
    "corroborated": "Three kinds of factor agree here, which is a reasonably firm reading.",
    "well corroborated": (
        "Four or more kinds of factor agree here. This is as well supported as this chart gets."
    ),
}


@dataclass(frozen=True)
class PlainReading:
    """What one house says, for someone who has not read the classics."""

    house: int
    topic: str
    """The area of life, in ordinary words."""
    governs: str
    """The fuller description of what the house covers."""
    headline: str
    """One sentence: the shape of this house's answer."""
    body: tuple[str, ...] = ()
    """Two or three sentences narrating the evidence."""
    limit: str = ""
    """What this reading does not claim."""
    karaka_note: str = ""
    """The natural significator, and what that adds."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "house": self.house,
            "topic": self.topic,
            "governs": self.governs,
            "headline": self.headline,
            "body": list(self.body),
            "limit": self.limit,
            "karaka_note": self.karaka_note,
        }


def _counted(evidence: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only what the gate itself would count.

    Disputed material is excluded here for the same reason it is excluded
    from the vote. If the prose counted it and the ledger did not, a reader
    comparing the two would find the engine contradicting itself.
    """
    return [e for e in evidence if not e.get("disputed")]


def _ordinal(n: int) -> str:
    # 11th/12th/13th are the exception the last-digit rule gets wrong.
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _join(items: Sequence[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def house_reading(
    house: int,
    topic: str,
    verdict: str,
    confidence: str,
    evidence: Sequence[dict[str, Any]],
) -> PlainReading:
    """Narrate one gated house finding in ordinary English.

    Everything said here is a restatement of `evidence`, which has already
    passed the gate. No judgement is added and none is softened.
    """
    counted = _counted(evidence)
    supporting = [e for e in counted if e.get("polarity", 0) > 0]
    opposing = [e for e in counted if e.get("polarity", 0) < 0]

    governs = HOUSE_GOVERNS.get(house, topic)
    place = f"the {_ordinal(house)} house"

    # ── headline ──────────────────────────────────────────────────────
    if "contested" in verdict:
        headline = (
            f"{place.capitalize()} pulls in two directions at once: parts of "
            f"it are genuinely well supported and other parts are genuinely "
            f"under strain, and neither cancels the other out."
        )
    elif "under strain" in verdict or (opposing and not supporting):
        headline = f"{place.capitalize()} is the harder ground in this chart."
    elif supporting and not opposing:
        headline = f"{place.capitalize()} is well supported, with nothing arguing against it."
    else:
        headline = f"{place.capitalize()} leans favourable on balance."

    # ── body ──────────────────────────────────────────────────────────
    body: list[str] = []

    def _phrases(items: Sequence[dict[str, Any]], positive: bool) -> list[str]:
        seen: list[str] = []
        for e in items:
            pair = _KIND_PLAIN.get(str(e.get("kind")))
            if not pair:
                continue
            phrase = pair[0] if positive else pair[1]
            if phrase not in seen:
                seen.append(phrase)
        return seen

    sup_phrases = _phrases(supporting, True)
    opp_phrases = _phrases(opposing, False)

    if sup_phrases:
        body.append(
            f"In its favour: {_join(sup_phrases)}."
            if len(sup_phrases) > 1
            else f"In its favour, {sup_phrases[0]}."
        )
    if opp_phrases:
        body.append(
            f"Against it: {_join(opp_phrases)}."
            if len(opp_phrases) > 1
            else f"Against it, {opp_phrases[0]}."
        )

    # Which texts this rests on — named, so the reader can go and look.
    texts = []
    for e in counted:
        src = str(e.get("source", ""))
        for name in (
            "Brihat Parashara Hora Shastra",
            "Phaladeepika",
            "Saravali",
            "Jataka Parijata",
            "Krishnamurti Paddhati",
            "Bhrigu Nandi Nadi",
        ):
            if name in src and name not in texts:
                texts.append(name)
    if texts:
        body.append(
            f"These rules come from {_join(texts)} — the citation for each one "
            f"is in the detail below."
        )

    # ── the limit ─────────────────────────────────────────────────────
    limit = _CONFIDENCE_PLAIN.get(confidence, "Read this as a direction rather than a conclusion.")
    disputed_count = len(evidence) - len(counted)
    if disputed_count:
        limit += (
            f" {disputed_count} further factor"
            f"{'s' if disputed_count > 1 else ''} appeared but "
            f"{'are' if disputed_count > 1 else 'is'} disputed between schools, "
            f"so {'they were' if disputed_count > 1 else 'it was'} not counted."
        )

    # ── the natural significator ──────────────────────────────────────
    karaka = BHAVA_KARAKA.get(house)
    karaka_note = ""
    if karaka:
        karaka_note = (
            f"{karaka} is the natural significator (karaka) of these matters "
            f"in any chart, whatever house it occupies here. Classical practice "
            f"is to read the house and its significator together, and to trust "
            f"the reading further when they agree."
        )

    return PlainReading(
        house=house,
        topic=topic,
        governs=governs,
        headline=headline,
        body=tuple(body),
        limit=limit,
        karaka_note=karaka_note,
    )


def withheld_reading(house: int, topic: str, reason: str) -> dict[str, Any]:
    """The plain form of a refusal.

    A withheld house is the most important thing this engine says, and it is
    the easiest to mistake for an error. It gets a full sentence.
    """
    governs = HOUSE_GOVERNS.get(house, topic)
    return {
        "house": house,
        "topic": topic,
        "governs": governs,
        "headline": (
            f"Nothing is claimed about the {_ordinal(house)} house, and that "
            f"is a finding rather than a gap."
        ),
        "body": [
            "This engine reports an area of life only where at least two "
            "different kinds of chart factor point the same way. Here they "
            "did not, so there is no reading to give.",
            "A chart that produced twelve confident answers would be telling "
            "you about its author rather than about the sky.",
        ],
        "limit": reason,
        "karaka_note": "",
    }
