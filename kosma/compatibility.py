"""
Compatibility between two or three charts.

Two modes, because they are genuinely different questions:

* ``relationship`` runs the full Ashtakoota (guna milan) out of 36, the doshas
  that classical matching checks, and the synastry that bears on partnership.
* ``friendship`` drops the kootas that exist to assess sexual and genetic
  compatibility (Yoni and Nadi) — they have nothing to say about a friendship —
  and reads the factors that do: birth-star relationship, temperament,
  mental affinity through the Moon lords, and the 3rd and 11th house overlays.

Everything routes through the same confirmation gate as the natal engine
(:func:`kosma.evidence.run_gate`), so a compatibility claim needs two
independent kinds of factor agreeing before it can be stated at all.

A note on what these numbers are
--------------------------------
Ashtakoota weighs eight factors and nothing else. It ignores the ascendants,
the 7th house and its lord, Venus and Mars, the dashas both people are running,
and every other thing a practitioner would actually look at. A score is an
input to a judgement, not the judgement. This module therefore leads with the
gated findings and reports the score as one factor among several, with its
critique attached.

Two of the eight also carry social weight worth naming plainly. **Varna** here
is a classification by the *Moon sign's element*, not a person's birth caste,
and it is not a statement about anyone's social standing. **Nadi** and
**Bhakoot** doshas are routinely used to refuse matches; the classical
cancellation conditions are checked and reported alongside, because they are
part of the method and are frequently omitted by people quoting the dosha.

Sources
-------
* Muhurta Chintamani ch. 1 and Brihat Parashara Hora Shastra ch. 5 —
  ashtakoota and the marriage kootas.
* Phaladeepika ch. 27 — kuja (mangal) dosha and its cancellations.
* Standard Tara Bala reckoning from the janma nakshatra.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import nakshatras as nak
from .aspects import aspects_cast
from .dignity import OWN_SIGNS, SIGN_LORDS, natural_relation
from .evidence import Evidence, GateOutcome, run_gate
from .vargas import d9
from .vedic_engine import (
    NAKSHATRAS,
    SIGNS,
    VEDIC_PLANETS,
    Chart,
    current_periods,
    vimshottari_dasha,
)

MODES = ("relationship", "friendship")

COMPAT_FACTOR_KINDS: tuple[str, ...] = (
    "koota",
    "dosha",
    "overlay",
    "cross_aspect",
    "moon_relationship",
    "lagna_relationship",
    "dasha_sync",
    "varga",
)


@dataclass(frozen=True)
class Person:
    """One participant: a label and a computed chart."""

    label: str
    chart: Chart

    @property
    def moon_nak_index(self) -> int:
        return NAKSHATRAS.index(self.chart.planets["Moon"].nakshatra)

    @property
    def moon_sign_index(self) -> int:
        return self.chart.planets["Moon"].sign_idx

    @property
    def moon_sign(self) -> str:
        return SIGNS[self.moon_sign_index]

    @property
    def moon_lord(self) -> str:
        return SIGN_LORDS[self.moon_sign]


# ── koota reference data ──────────────────────────────────────────────

# Varna by the Moon sign's element. This is a temperament classification in
# Jyotisha, assigned by the sky and not by anyone's family or social caste.
_VARNA_RANK: dict[str, int] = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}
_VARNA_BY_ELEMENT: dict[int, str] = {
    3: "Brahmin",  # water: Cancer, Scorpio, Pisces
    0: "Kshatriya",  # fire: Aries, Leo, Sagittarius
    1: "Vaishya",  # earth: Taurus, Virgo, Capricorn
    2: "Shudra",  # air: Gemini, Libra, Aquarius
}

# Vashya groups. Sagittarius and Capricorn split at 15 degrees.
_VASHYA_SIMPLE: dict[int, str] = {
    0: "chatushpada",  # Aries
    1: "chatushpada",  # Taurus
    2: "manava",  # Gemini
    3: "jalachara",  # Cancer
    4: "vanachara",  # Leo
    5: "manava",  # Virgo
    6: "manava",  # Libra
    7: "keeta",  # Scorpio
    10: "manava",  # Aquarius
    11: "jalachara",  # Pisces
}

_VASHYA_SCORES: dict[frozenset[str], float] = {
    frozenset({"chatushpada"}): 2.0,
    frozenset({"manava"}): 2.0,
    frozenset({"jalachara"}): 2.0,
    frozenset({"vanachara"}): 2.0,
    frozenset({"keeta"}): 2.0,
    frozenset({"chatushpada", "manava"}): 1.0,
    frozenset({"chatushpada", "jalachara"}): 1.0,
    frozenset({"chatushpada", "vanachara"}): 0.0,
    frozenset({"chatushpada", "keeta"}): 1.0,
    frozenset({"manava", "jalachara"}): 1.0,
    frozenset({"manava", "vanachara"}): 0.0,
    frozenset({"manava", "keeta"}): 1.0,
    frozenset({"jalachara", "vanachara"}): 1.0,
    frozenset({"jalachara", "keeta"}): 0.5,
    frozenset({"vanachara", "keeta"}): 1.0,
}

_VASHYA_VARIANT_NOTE = (
    "Vashya tables differ appreciably between authors. This is one documented "
    "variant; another would move the total by at most two points."
)

# Tara names by position in the nine-fold count from the janma nakshatra.
_TARA_NAMES = (
    "Janma",
    "Sampat",
    "Vipat",
    "Kshema",
    "Pratyari",
    "Sadhaka",
    "Vadha",
    "Mitra",
    "Ati-Mitra",
)
_INAUSPICIOUS_TARA = (3, 5, 7)  # Vipat, Pratyari, Vadha

# The seven sworn-enemy yoni pairs.
_YONI_ENEMIES: tuple[frozenset[str], ...] = (
    frozenset({"cow", "tiger"}),
    frozenset({"elephant", "lion"}),
    frozenset({"horse", "buffalo"}),
    frozenset({"dog", "deer"}),
    frozenset({"serpent", "mongoose"}),
    frozenset({"monkey", "sheep"}),
    frozenset({"cat", "rat"}),
)

_YONI_SIMPLIFICATION = (
    "The full Yoni matrix grades fourteen animals as friendly (3), neutral (2) "
    "or hostile (1). This implementation resolves only identical (4) and the "
    "seven sworn-enemy pairs (0), scoring everything else neutral rather than "
    "asserting a grade it cannot source cell by cell."
)

# Nadi by nakshatra index, in the standard zigzag.
_NADI_ADI = (0, 5, 6, 11, 12, 17, 18, 23, 24)
_NADI_MADHYA = (1, 4, 7, 10, 13, 16, 19, 22, 25)
_NADI_ANTYA = (2, 3, 8, 9, 14, 15, 20, 21, 26)

_GANA_SCORES: dict[frozenset[str], float] = {
    frozenset({"deva"}): 6.0,
    frozenset({"manushya"}): 6.0,
    frozenset({"rakshasa"}): 6.0,
    frozenset({"deva", "manushya"}): 5.0,
    frozenset({"deva", "rakshasa"}): 1.0,
    frozenset({"manushya", "rakshasa"}): 0.0,
}

_MAITRI_SCORES: dict[frozenset[str], float] = {
    frozenset({"friend"}): 5.0,
    frozenset({"friend", "neutral"}): 4.0,
    frozenset({"neutral"}): 3.0,
    frozenset({"neutral", "enemy"}): 1.0,
    frozenset({"friend", "enemy"}): 0.5,
    frozenset({"enemy"}): 0.0,
}

# Moon-sign distances that classically void the Bhakoot koota.
_BHAKOOT_BAD = (frozenset({2, 12}), frozenset({5, 9}), frozenset({6, 8}))

# Houses from lagna, Moon and Venus in which Mars raises kuja dosha.
_MANGAL_HOUSES = (1, 2, 4, 7, 8, 12)


@dataclass(frozen=True)
class Koota:
    """One scored factor, with the rule and source behind it."""

    name: str
    score: float
    maximum: float
    detail: str
    rule: str
    source: str
    dosha: str | None = None
    variant_note: str | None = None

    @property
    def fraction(self) -> float:
        return self.score / self.maximum if self.maximum else 0.0

    @property
    def full(self) -> bool:
        return self.score >= self.maximum

    @property
    def void(self) -> bool:
        return self.score == 0.0


@dataclass(frozen=True)
class Dosha:
    """An affliction check, with whatever cancellations were found."""

    name: str
    present: bool
    detail: str
    cancellations: tuple[str, ...]
    source: str
    note: str

    @property
    def cancelled(self) -> bool:
        return self.present and bool(self.cancellations)

    @property
    def status(self) -> str:
        if not self.present:
            return "absent"
        return "present but cancelled" if self.cancellations else "present, no cancellation found"


# ── the eight kootas ──────────────────────────────────────────────────


def _varna(a: Person, b: Person) -> Koota:
    va = _VARNA_BY_ELEMENT[a.moon_sign_index % 4]
    vb = _VARNA_BY_ELEMENT[b.moon_sign_index % 4]
    forward = _VARNA_RANK[va] >= _VARNA_RANK[vb]
    score = 1.0 if forward else 0.0
    return Koota(
        name="Varna",
        score=score,
        maximum=1.0,
        detail=(
            f"{a.label} is {va} and {b.label} is {vb} by Moon-sign element. "
            f"The rule scores {'a point' if forward else 'nothing'} in this "
            f"order; reversing the two would score "
            f"{'nothing' if forward else 'a point'}."
        ),
        rule=(
            "Varna is taken from the Moon sign's element (water Brahmin, fire "
            "Kshatriya, earth Vaishya, air Shudra). Classically the first-named "
            "partner's varna should equal or exceed the other's."
        ),
        source="Muhurta Chintamani ch. 1",
        variant_note=(
            "This is a classification by the sky, not by anyone's birth caste or "
            "social standing, and it carries no such meaning here. The rule is "
            "also directional and gendered in origin; KOSMA assumes no genders, "
            "so the order you entered decides it and both directions are shown. "
            "Many contemporary practitioners drop this koota entirely."
        ),
    )


def _vashya_group(sign_idx: int, deg: float) -> str:
    if sign_idx == 8:  # Sagittarius splits at 15 degrees
        return "manava" if deg < 15.0 else "chatushpada"
    if sign_idx == 9:  # Capricorn splits at 15 degrees
        return "chatushpada" if deg < 15.0 else "jalachara"
    return _VASHYA_SIMPLE[sign_idx]


def _vashya(a: Person, b: Person) -> Koota:
    ga = _vashya_group(a.moon_sign_index, a.chart.planets["Moon"].deg_in_sign)
    gb = _vashya_group(b.moon_sign_index, b.chart.planets["Moon"].deg_in_sign)
    score = _VASHYA_SCORES[frozenset({ga, gb})]
    return Koota(
        name="Vashya",
        score=score,
        maximum=2.0,
        detail=f"{a.label} is {ga} and {b.label} is {gb} by Moon sign",
        rule=(
            "Moon signs are grouped as quadruped, human, watery, wild or insect, "
            "and scored on how naturally one holds sway over the other."
        ),
        source="Muhurta Chintamani ch. 1",
        variant_note=_VASHYA_VARIANT_NOTE,
    )


def _tara_count(from_idx: int, to_idx: int) -> tuple[int, str, bool]:
    count = ((to_idx - from_idx) % 27) + 1
    position = count % 9 or 9
    return position, _TARA_NAMES[position - 1], position not in _INAUSPICIOUS_TARA


def _tara(a: Person, b: Person) -> Koota:
    pa, na, oka = _tara_count(a.moon_nak_index, b.moon_nak_index)
    pb, nb, okb = _tara_count(b.moon_nak_index, a.moon_nak_index)
    score = 3.0 if (oka and okb) else (1.5 if (oka or okb) else 0.0)
    return Koota(
        name="Tara",
        score=score,
        maximum=3.0,
        detail=(
            f"counting from {a.label} to {b.label} gives {na} ({pa}), and back gives {nb} ({pb})"
        ),
        rule=(
            "Count from each birth star to the other and reduce by nine. The "
            "3rd (Vipat), 5th (Pratyari) and 7th (Vadha) positions are "
            "inauspicious; full marks need both directions clear."
        ),
        source="Standard Tara Bala reckoning; Muhurta Chintamani ch. 1",
    )


def _yoni(a: Person, b: Person) -> Koota:
    ya = nak.by_index(a.moon_nak_index).yoni
    yb = nak.by_index(b.moon_nak_index).yoni
    if ya == yb:
        score, verdict = 4.0, "the same yoni"
    elif frozenset({ya, yb}) in _YONI_ENEMIES:
        score, verdict = 0.0, "a sworn-enemy pair"
    else:
        score, verdict = 2.0, "neither identical nor sworn enemies"
    return Koota(
        name="Yoni",
        score=score,
        maximum=4.0,
        detail=f"{a.label} is {ya} and {b.label} is {yb} — {verdict}",
        rule=(
            "Each nakshatra carries an animal (yoni). Identical yonis score "
            "full; the seven sworn-enemy pairs score nothing."
        ),
        source="Muhurta Chintamani ch. 1",
        variant_note=_YONI_SIMPLIFICATION,
    )


def _graha_maitri(a: Person, b: Person) -> Koota:
    la, lb = a.moon_lord, b.moon_lord
    if la == lb:
        return Koota(
            name="Graha Maitri",
            score=5.0,
            maximum=5.0,
            detail=f"both Moon signs are ruled by {la}",
            rule="The friendship of the two Moon-sign lords, taken both ways.",
            source="Muhurta Chintamani ch. 1",
        )
    rel_ab = natural_relation(la, lb)
    rel_ba = natural_relation(lb, la)
    score = _MAITRI_SCORES.get(frozenset({rel_ab, rel_ba}), 3.0)
    return Koota(
        name="Graha Maitri",
        score=score,
        maximum=5.0,
        detail=(
            f"{la} (ruling {a.label}'s Moon) counts {lb} a {rel_ab}, and {lb} "
            f"counts {la} a {rel_ba}"
        ),
        rule="The natural friendship of the two Moon-sign lords, taken both ways.",
        source="Brihat Parashara Hora Shastra ch. 3; Muhurta Chintamani ch. 1",
    )


def _gana(a: Person, b: Person) -> Koota:
    ga = nak.by_index(a.moon_nak_index).gana
    gb = nak.by_index(b.moon_nak_index).gana
    score = _GANA_SCORES[frozenset({ga, gb})]
    return Koota(
        name="Gana",
        score=score,
        maximum=6.0,
        detail=f"{a.label} is {ga} gana and {b.label} is {gb} gana",
        rule=(
            "Temperament class from the birth star: deva, manushya or rakshasa. "
            "Alike scores full; deva with rakshasa scores almost nothing."
        ),
        source="Muhurta Chintamani ch. 1",
        variant_note=(
            "Some authors make this directional, scoring a deva-manushya pair "
            "differently depending on which partner holds which."
        ),
    )


def _bhakoot(a: Person, b: Person) -> Koota:
    d_ab = ((b.moon_sign_index - a.moon_sign_index) % 12) + 1
    d_ba = ((a.moon_sign_index - b.moon_sign_index) % 12) + 1
    pair = frozenset({d_ab, d_ba})
    bad = pair in _BHAKOOT_BAD
    return Koota(
        name="Bhakoot",
        score=0.0 if bad else 7.0,
        maximum=7.0,
        detail=(
            f"{a.label}'s Moon in {a.moon_sign} and {b.label}'s in "
            f"{b.moon_sign} stand {d_ab}/{d_ba} from each other"
            + (" — a voiding pair" if bad else "")
        ),
        rule=(
            "The Moon signs' mutual distance. The 2/12, 5/9 and 6/8 pairings "
            "void this koota; every other distance scores full."
        ),
        source="Muhurta Chintamani ch. 1",
        dosha="Bhakoot dosha" if bad else None,
    )


def _nadi_of(nak_index: int) -> str:
    if nak_index in _NADI_ADI:
        return "Adi"
    if nak_index in _NADI_MADHYA:
        return "Madhya"
    return "Antya"


def _nadi(a: Person, b: Person) -> Koota:
    na, nb = _nadi_of(a.moon_nak_index), _nadi_of(b.moon_nak_index)
    same = na == nb
    return Koota(
        name="Nadi",
        score=0.0 if same else 8.0,
        maximum=8.0,
        detail=f"{a.label} is {na} nadi and {b.label} is {nb} nadi",
        rule=(
            "Constitutional type from the birth star: Adi, Madhya or Antya. "
            "The same nadi voids the koota; different nadis score full."
        ),
        source="Muhurta Chintamani ch. 1",
        dosha="Nadi dosha" if same else None,
    )


ASHTAKOOTA = (_varna, _vashya, _tara, _yoni, _graha_maitri, _gana, _bhakoot, _nadi)
# The friendship subset: what remains once the kootas that exist to assess
# sexual and genetic compatibility are removed.
MAITRI_KOOTAS = (_vashya, _tara, _graha_maitri, _gana, _bhakoot)


@dataclass
class Milan:
    """A koota tally, with its own critique attached."""

    kootas: list[Koota]
    scheme: str
    critique: str

    @property
    def total(self) -> float:
        return round(sum(k.score for k in self.kootas), 2)

    @property
    def maximum(self) -> float:
        return round(sum(k.maximum for k in self.kootas), 2)

    @property
    def percentage(self) -> float:
        return round(self.total / self.maximum * 100, 1) if self.maximum else 0.0

    @property
    def voided(self) -> list[Koota]:
        return [k for k in self.kootas if k.void]


_ASHTAKOOTA_CRITIQUE = (
    "Ashtakoota weighs eight factors from the Moon's nakshatra and sign, and "
    "nothing else. It does not look at either ascendant, the 7th house or its "
    "lord, Venus, Mars, the dashas in force, or the charts as wholes. A high "
    "score is not a guarantee and a low one is not a verdict — practitioners "
    "differ sharply on how much it should decide. Read the gated findings "
    "below it, which draw on the rest of both charts."
)

_MAITRI_CRITIQUE = (
    "This is not a classical named scheme. It is the ashtakoota with Yoni and "
    "Nadi removed, because those two exist to assess sexual and genetic "
    "compatibility and say nothing about a friendship, and with Varna removed "
    "because its rule is directional and marriage-shaped. What remains — birth "
    "star, temperament, the Moon lords' friendship, and the Moon signs' "
    "distance — are the classical factors that do bear on affinity. The total "
    "is KOSMA's construction from classical parts, so treat the parts as "
    "authoritative and the sum as a convenience."
)


def guna_milan(a: Person, b: Person) -> Milan:
    """The full eight-fold marriage tally out of 36."""
    return Milan(
        kootas=[fn(a, b) for fn in ASHTAKOOTA],
        scheme="Ashtakoota (guna milan)",
        critique=_ASHTAKOOTA_CRITIQUE,
    )


def maitri_milan(a: Person, b: Person) -> Milan:
    """The friendship subset, with the marriage-specific kootas removed."""
    return Milan(
        kootas=[fn(a, b) for fn in MAITRI_KOOTAS],
        scheme="Maitri factors (friendship subset)",
        critique=_MAITRI_CRITIQUE,
    )


# ── doshas ────────────────────────────────────────────────────────────

_DOSHA_FRAMING = (
    "Doshas are checked here because they are part of the classical method and "
    "because the cancellation conditions are routinely omitted by people who "
    "quote them. A dosha is a flag to examine, not a disqualification of anyone."
)


def mangal_dosha(person: Person) -> Dosha:
    """Kuja dosha: Mars in the 1st, 2nd, 4th, 7th, 8th or 12th."""
    chart = person.chart
    mars = chart.planets["Mars"]
    references: list[str] = []

    if mars.house in _MANGAL_HOUSES:
        references.append(f"the {_ord(mars.house)} from the lagna")
    from_moon = ((mars.sign_idx - chart.planets["Moon"].sign_idx) % 12) + 1
    if from_moon in _MANGAL_HOUSES:
        references.append(f"the {_ord(from_moon)} from the Moon")
    from_venus = ((mars.sign_idx - chart.planets["Venus"].sign_idx) % 12) + 1
    if from_venus in _MANGAL_HOUSES:
        references.append(f"the {_ord(from_venus)} from Venus")

    if not references:
        return Dosha(
            name="Mangal dosha",
            present=False,
            detail=(
                f"Mars sits in the {_ord(mars.house)} from the lagna, outside "
                f"the 1st, 2nd, 4th, 7th, 8th and 12th"
            ),
            cancellations=(),
            source="Phaladeepika ch. 27",
            note=_DOSHA_FRAMING,
        )

    cancellations: list[str] = []
    if mars.sign in OWN_SIGNS["Mars"]:
        cancellations.append(f"Mars is in its own sign {mars.sign}")
    if mars.sign == "Capricorn":
        cancellations.append("Mars is exalted in Capricorn")
    if mars.sign_idx == chart.planets["Saturn"].sign_idx:
        cancellations.append("Mars is conjunct Saturn, which classically restrains it")
    if mars.sign_idx == chart.planets["Jupiter"].sign_idx:
        cancellations.append("Mars is conjunct Jupiter, which classically restrains it")
    for asp in aspects_cast(chart):
        if asp.source == "Jupiter" and asp.target_house == mars.house and not asp.disputed:
            cancellations.append("Jupiter aspects Mars")
            break

    return Dosha(
        name="Mangal dosha",
        present=True,
        detail=f"Mars occupies {_and_join(references)}",
        cancellations=tuple(dict.fromkeys(cancellations)),
        source="Phaladeepika ch. 27",
        note=_DOSHA_FRAMING,
    )


def mutual_mangal(a: Person, b: Person) -> Dosha:
    """The classical mutual-cancellation rule for kuja dosha."""
    da, db = mangal_dosha(a), mangal_dosha(b)
    if da.present and db.present:
        return Dosha(
            name="Mangal dosha (mutual)",
            present=True,
            detail=f"both {a.label} and {b.label} carry it",
            cancellations=(
                "Both charts carry the dosha, which classical practice treats as "
                "mutually cancelling.",
            ),
            source="Phaladeepika ch. 27",
            note=_DOSHA_FRAMING,
        )
    if not da.present and not db.present:
        return Dosha(
            name="Mangal dosha (mutual)",
            present=False,
            detail="neither chart carries it",
            cancellations=(),
            source="Phaladeepika ch. 27",
            note=_DOSHA_FRAMING,
        )
    who = a.label if da.present else b.label
    carried = da if da.present else db
    return Dosha(
        name="Mangal dosha (mutual)",
        present=True,
        detail=f"{who} carries it and the other does not — {carried.detail}",
        cancellations=carried.cancellations,
        source="Phaladeepika ch. 27",
        note=_DOSHA_FRAMING,
    )


def bhakoot_dosha(a: Person, b: Person, koota: Koota) -> Dosha:
    if not koota.void:
        return Dosha(
            name="Bhakoot dosha",
            present=False,
            detail=koota.detail,
            cancellations=(),
            source="Muhurta Chintamani ch. 1",
            note=_DOSHA_FRAMING,
        )
    cancellations: list[str] = []
    if a.moon_lord == b.moon_lord:
        cancellations.append(f"both Moon signs are ruled by {a.moon_lord}")
    elif natural_relation(a.moon_lord, b.moon_lord) == "friend":
        cancellations.append(f"the Moon lords {a.moon_lord} and {b.moon_lord} are friends")
    if a.chart.planets["Moon"].nak_lord == b.chart.planets["Moon"].nak_lord:
        cancellations.append("both Moons share a nakshatra lord")
    return Dosha(
        name="Bhakoot dosha",
        present=True,
        detail=koota.detail,
        cancellations=tuple(cancellations),
        source="Muhurta Chintamani ch. 1",
        note=_DOSHA_FRAMING,
    )


def nadi_dosha(a: Person, b: Person, koota: Koota) -> Dosha:
    if not koota.void:
        return Dosha(
            name="Nadi dosha",
            present=False,
            detail=koota.detail,
            cancellations=(),
            source="Muhurta Chintamani ch. 1",
            note=_DOSHA_FRAMING,
        )
    cancellations: list[str] = []
    if a.moon_sign_index != b.moon_sign_index:
        cancellations.append("the Moon signs differ")
    if a.moon_nak_index != b.moon_nak_index:
        cancellations.append("the birth stars differ")
    elif a.chart.planets["Moon"].pada != b.chart.planets["Moon"].pada:
        cancellations.append("the birth star is shared but the padas differ")
    if a.moon_lord == b.moon_lord:
        cancellations.append(f"both Moon signs are ruled by {a.moon_lord}")
    return Dosha(
        name="Nadi dosha",
        present=True,
        detail=koota.detail,
        cancellations=tuple(cancellations),
        source="Muhurta Chintamani ch. 1",
        note=_DOSHA_FRAMING,
    )


# ── synastry ──────────────────────────────────────────────────────────

SUPPORTIVE_OVERLAY = (1, 4, 5, 7, 9, 10, 11)
FRICTION_OVERLAY = (6, 8, 12)

_OVERLAY_THEME: dict[int, str] = {
    1: "identity and how the other is seen",
    2: "money, speech and family",
    3: "everyday contact and initiative",
    4: "home and emotional ground",
    5: "romance, play and creativity",
    6: "duty, friction and service",
    7: "partnership itself",
    8: "crisis, dependence and the hidden",
    9: "shared belief and direction",
    10: "standing, ambition and public life",
    11: "friendship, gain and networks",
    12: "loss, retreat and what goes unspoken",
}


@dataclass(frozen=True)
class Overlay:
    """Where one person's planet lands in the other's houses."""

    planet: str
    owner: str
    into_house: int
    host: str
    theme: str
    polarity: int


def overlays(a: Person, b: Person) -> list[Overlay]:
    """Every planet of ``a`` placed into ``b``'s whole-sign houses."""
    out: list[Overlay] = []
    for name in VEDIC_PLANETS:
        sign_idx = a.chart.planets[name].sign_idx
        house = ((sign_idx - b.chart.ascendant_sign_idx) % 12) + 1
        if house in FRICTION_OVERLAY:
            polarity = -1
        elif house in SUPPORTIVE_OVERLAY:
            polarity = 1
        else:
            polarity = 0
        out.append(
            Overlay(
                planet=name,
                owner=a.label,
                into_house=house,
                host=b.label,
                theme=_OVERLAY_THEME[house],
                polarity=polarity,
            )
        )
    return out


@dataclass(frozen=True)
class CrossAspect:
    """Drishti cast from one chart onto a point in the other."""

    source_planet: str
    source_owner: str
    target: str
    target_owner: str
    rule: str
    polarity: int


_BENEFIC_FOR_CROSS = ("Jupiter", "Venus", "Mercury", "Moon")
_CROSS_TARGETS = ("Ascendant", "Moon", "Venus", "Sun")


def cross_aspects(a: Person, b: Person) -> list[CrossAspect]:
    """Aspects from ``a``'s planets onto ``b``'s sensitive points."""
    targets: dict[str, int] = {"Ascendant": b.chart.ascendant_sign_idx}
    for name in ("Moon", "Venus", "Sun"):
        targets[name] = b.chart.planets[name].sign_idx

    out: list[CrossAspect] = []
    for asp in aspects_cast(a.chart):
        if asp.disputed:
            continue
        # Re-resolve the aspect's landing sign independently of A's lagna.
        source_sign = a.chart.planets[asp.source].sign_idx
        landing = (source_sign + asp.distance - 1) % 12
        for target_name, target_sign in targets.items():
            if landing != target_sign:
                continue
            out.append(
                CrossAspect(
                    source_planet=asp.source,
                    source_owner=a.label,
                    target=target_name,
                    target_owner=b.label,
                    rule=asp.rule,
                    polarity=1 if asp.source in _BENEFIC_FOR_CROSS else -1,
                )
            )
    return out


@dataclass(frozen=True)
class DashaSync:
    """How the two running dasha cycles relate."""

    a_maha: str | None
    a_antar: str | None
    b_maha: str | None
    b_antar: str | None
    shared: tuple[str, ...]
    relation: str
    polarity: int
    detail: str


def dasha_sync(a: Person, b: Person, now_jd: float) -> DashaSync:
    """Compare the periods both people are actually running."""

    def current(p: Person) -> tuple[str | None, str | None]:
        dashas = vimshottari_dasha(p.chart.planets["Moon"].longitude, p.chart.jd)
        maha, antar, _ = current_periods(dashas, now_jd)
        return (maha[0] if maha else None), (antar[0] if antar else None)

    a_maha, a_antar = current(a)
    b_maha, b_antar = current(b)

    shared = tuple(
        sorted({x for x in (a_maha, a_antar) if x} & {x for x in (b_maha, b_antar) if x})
    )
    if a_maha and b_maha:
        relation = "same lord" if a_maha == b_maha else natural_relation(a_maha, b_maha)
    else:
        relation = "unknown"

    polarity = {"same lord": 1, "friend": 1, "neutral": 0, "enemy": -1}.get(relation, 0)
    detail = (
        f"{a.label} runs {a_maha}/{a_antar} and {b.label} runs {b_maha}/{b_antar}; "
        f"the mahadasha lords are {relation}"
        + (f"; they share {_and_join(list(shared))}" if shared else "")
    )
    return DashaSync(
        a_maha=a_maha,
        a_antar=a_antar,
        b_maha=b_maha,
        b_antar=b_antar,
        shared=shared,
        relation=relation,
        polarity=polarity,
        detail=detail,
    )


# ── topics and the gate ───────────────────────────────────────────────

RELATIONSHIP_TOPICS: dict[str, str] = {
    "emotional rapport": "how the two temperaments meet day to day",
    "affection and attraction": "Venus, Mars, and the 5th and 7th overlays",
    "communication": "Mercury, the 3rd, and how information passes between them",
    "shared direction": "Jupiter, the 9th, and whether the two point the same way",
    "friction": "the 6th, 8th and 12th overlays, and hard cross-aspects",
    "durability": "Saturn, the dashas in force, and what holds over time",
}

FRIENDSHIP_TOPICS: dict[str, str] = {
    "emotional rapport": "how the two temperaments meet day to day",
    "communication": "Mercury, the 3rd, and how information passes between them",
    "shared direction": "Jupiter, the 9th, and whether the two point the same way",
    "mutual gain": "the 11th and 3rd overlays — what each brings the other",
    "friction": "the 6th, 8th and 12th overlays, and hard cross-aspects",
    "durability": "Saturn, the dashas in force, and what holds over time",
}

# Which planets and houses bear on each topic.
_TOPIC_PLANETS: dict[str, tuple[str, ...]] = {
    "emotional rapport": ("Moon",),
    "affection and attraction": ("Venus", "Mars"),
    "communication": ("Mercury",),
    "shared direction": ("Jupiter", "Sun"),
    "friction": ("Saturn", "Mars", "Rahu", "Ketu"),
    "durability": ("Saturn",),
    "mutual gain": ("Jupiter", "Venus", "Mercury"),
}
_TOPIC_HOUSES: dict[str, tuple[int, ...]] = {
    "emotional rapport": (4, 1),
    "affection and attraction": (5, 7),
    "communication": (3, 2),
    "shared direction": (9, 10),
    "friction": (6, 8, 12),
    "durability": (10, 11),
    "mutual gain": (11, 3),
}
_TOPIC_KOOTAS: dict[str, tuple[str, ...]] = {
    "emotional rapport": ("Gana", "Bhakoot", "Graha Maitri"),
    "affection and attraction": ("Yoni", "Vashya"),
    "communication": ("Graha Maitri", "Tara"),
    "shared direction": ("Varna", "Graha Maitri"),
    "friction": ("Bhakoot", "Nadi"),
    "durability": ("Nadi", "Bhakoot", "Tara"),
    "mutual gain": ("Tara", "Vashya"),
}


@dataclass(frozen=True)
class TopicResult:
    """One compatibility topic after the gate has ruled on it."""

    topic: str
    description: str
    outcome: GateOutcome
    evidence: tuple[Evidence, ...]

    @property
    def passed(self) -> bool:
        return self.outcome.passed

    @property
    def verdict(self) -> str:
        return self.outcome.verdict

    @property
    def confidence(self) -> str:
        return self.outcome.confidence

    @property
    def citations(self) -> tuple[str, ...]:
        return tuple(e.id for e in self.evidence)


@dataclass
class PairReport:
    """Everything computed for one pair."""

    a: str
    b: str
    mode: str
    milan: Milan
    doshas: list[Dosha]
    overlays_ab: list[Overlay]
    overlays_ba: list[Overlay]
    cross_ab: list[CrossAspect]
    cross_ba: list[CrossAspect]
    sync: DashaSync
    findings: list[TopicResult] = field(default_factory=list)
    withheld: list[TopicResult] = field(default_factory=list)
    ledger: list[Evidence] = field(default_factory=list)
    navamsa_note: str = ""


class _CompatLedger:
    """Accumulates compatibility evidence with quotable, topic-scoped ids."""

    def __init__(self) -> None:
        self.items: list[Evidence] = []
        self._counters: dict[str, int] = {}

    def add(
        self,
        *,
        topic: str,
        kind: str,
        statement: str,
        basis: str,
        source: str,
        polarity: int,
        weight: float = 1.0,
        disputed: bool = False,
    ) -> Evidence:
        code = _topic_code(topic)
        n = self._counters.get(code, 0) + 1
        self._counters[code] = n
        item = Evidence(
            id=f"{code}-{n}",
            kind=kind,
            house=0,  # compatibility evidence is topic-scoped, not house-scoped
            statement=statement,
            basis=basis,
            source=source,
            polarity=polarity,
            weight=weight,
            disputed=disputed,
        )
        self.items.append(item)
        return item

    def for_topic(self, topic: str) -> tuple[Evidence, ...]:
        code = _topic_code(topic)
        return tuple(e for e in self.items if e.id.startswith(f"{code}-"))


def _topic_code(topic: str) -> str:
    """A short stable prefix for evidence ids, e.g. 'emotional rapport' -> 'ER'."""
    return "".join(word[0] for word in topic.split()).upper()


def _collect_topic_evidence(
    led: _CompatLedger,
    topic: str,
    a: Person,
    b: Person,
    milan: Milan,
    doshas: list[Dosha],
    ov_ab: list[Overlay],
    ov_ba: list[Overlay],
    cross: list[CrossAspect],
    sync: DashaSync,
) -> None:
    """Gather every factor bearing on one topic."""
    planets = _TOPIC_PLANETS.get(topic, ())
    houses = _TOPIC_HOUSES.get(topic, ())
    koota_names = _TOPIC_KOOTAS.get(topic, ())

    # 1. kootas relevant to this topic
    for k in milan.kootas:
        if k.name not in koota_names:
            continue
        if k.full:
            polarity = 1
        elif k.void:
            polarity = -1
        else:
            polarity = 0
        led.add(
            topic=topic,
            kind="koota",
            statement=f"{k.name} scores {k.score:g} of {k.maximum:g}",
            basis=f"{k.detail}; rule: {k.rule}",
            source=k.source,
            polarity=polarity,
            weight=1.2,
            disputed=bool(k.variant_note),
        )

    # 2. doshas that bear on friction or durability
    if topic in ("friction", "durability", "emotional rapport"):
        for d in doshas:
            if not d.present:
                continue
            led.add(
                topic=topic,
                kind="dosha",
                statement=f"{d.name} is {d.status}",
                basis=f"{d.detail}"
                + (
                    f"; cancelled because {_and_join(list(d.cancellations))}"
                    if d.cancellations
                    else ""
                ),
                source=d.source,
                polarity=0 if d.cancelled else -1,
                weight=1.4,
            )

    # 3. house overlays in both directions
    for overlay_set, owner, host in ((ov_ab, a, b), (ov_ba, b, a)):
        for ov in overlay_set:
            if ov.into_house not in houses and ov.planet not in planets:
                continue
            if ov.into_house not in houses:
                continue
            led.add(
                topic=topic,
                kind="overlay",
                statement=(
                    f"{owner.label}'s {ov.planet} falls in {host.label}'s "
                    f"{_ord(ov.into_house)} house"
                ),
                basis=f"that house governs {ov.theme}",
                source="Synastry by whole-sign overlay from each natal lagna",
                polarity=ov.polarity,
                weight=1.0,
            )

    # 4. cross-chart drishti onto sensitive points
    for ca in cross:
        if ca.source_planet not in planets:
            continue
        led.add(
            topic=topic,
            kind="cross_aspect",
            statement=(
                f"{ca.source_owner}'s {ca.source_planet} aspects {ca.target_owner}'s {ca.target}"
            ),
            basis=ca.rule,
            source="Brihat Parashara Hora Shastra ch. 26, applied across charts",
            polarity=ca.polarity,
            weight=1.1,
        )

    # 5. the Moon relationship, which underlies rapport
    if topic in ("emotional rapport", "friction"):
        d_ab = ((b.moon_sign_index - a.moon_sign_index) % 12) + 1
        polarity = 1 if d_ab in (1, 3, 5, 7, 9, 11) else -1
        led.add(
            topic=topic,
            kind="moon_relationship",
            statement=(
                f"{b.label}'s Moon stands {_ord(d_ab)} from {a.label}'s "
                f"({a.moon_sign} to {b.moon_sign})"
            ),
            basis=(
                f"ruled by {a.moon_lord} and {b.moon_lord}, who are naturally "
                f"{natural_relation(a.moon_lord, b.moon_lord)}"
            ),
            source="Gochara and rashi relationship reckoning",
            polarity=polarity,
            weight=1.1,
        )

    # 6. the ascendant relationship, which underlies how they read each other
    if topic in ("emotional rapport", "communication", "shared direction"):
        la = SIGN_LORDS[a.chart.ascendant_sign]
        lb = SIGN_LORDS[b.chart.ascendant_sign]
        rel = "the same lord" if la == lb else natural_relation(la, lb)
        polarity = 1 if rel in ("the same lord", "friend") else (-1 if rel == "enemy" else 0)
        led.add(
            topic=topic,
            kind="lagna_relationship",
            statement=(
                f"{a.label} rises in {a.chart.ascendant_sign} and {b.label} in "
                f"{b.chart.ascendant_sign}"
            ),
            basis=f"their lords {la} and {lb} are {rel}",
            source="Brihat Parashara Hora Shastra ch. 3 (natural friendship)",
            polarity=polarity,
            weight=1.1,
        )

    # 7. the dashas both are actually running
    if topic in ("durability", "shared direction"):
        led.add(
            topic=topic,
            kind="dasha_sync",
            statement=f"the running mahadasha lords are {sync.relation}",
            basis=sync.detail,
            source="Vimshottari dasha, both charts taken at the same moment",
            polarity=sync.polarity,
            weight=1.2,
        )

    # 8. the navamsa, which classical practice reads for partnership
    if topic in ("affection and attraction", "durability", "mutual gain"):
        na = d9(a.chart.ascendant_sign_idx, a.chart.ascendant_deg)
        nb = d9(b.chart.ascendant_sign_idx, b.chart.ascendant_deg)
        distance = ((nb - na) % 12) + 1
        polarity = 1 if distance in (1, 3, 5, 7, 9, 11) else -1
        led.add(
            topic=topic,
            kind="varga",
            statement=(
                f"the D9 ascendants are {SIGNS[na]} and {SIGNS[nb]}, "
                f"{_ord(distance)} from each other"
            ),
            basis=(
                "the navamsa is read for marriage and inner disposition; an odd "
                "distance between the D9 lagnas is classically easier than an even one"
            ),
            source="Brihat Parashara Hora Shastra ch. 6 (navamsa)",
            polarity=polarity,
            weight=1.0,
        )


def compare(a: Person, b: Person, now_jd: float, mode: str = "relationship") -> PairReport:
    """Compare two charts and let only what clears the gate through."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    milan = guna_milan(a, b) if mode == "relationship" else maitri_milan(a, b)
    by_name = {k.name: k for k in guna_milan(a, b).kootas}

    doshas = [
        mutual_mangal(a, b),
        bhakoot_dosha(a, b, by_name["Bhakoot"]),
    ]
    if mode == "relationship":
        doshas.append(nadi_dosha(a, b, by_name["Nadi"]))

    ov_ab = overlays(a, b)
    ov_ba = overlays(b, a)
    cross = cross_aspects(a, b) + cross_aspects(b, a)
    sync = dasha_sync(a, b, now_jd)

    topics = RELATIONSHIP_TOPICS if mode == "relationship" else FRIENDSHIP_TOPICS
    led = _CompatLedger()
    for topic in topics:
        _collect_topic_evidence(led, topic, a, b, milan, doshas, ov_ab, ov_ba, cross, sync)

    report = PairReport(
        a=a.label,
        b=b.label,
        mode=mode,
        milan=milan,
        doshas=doshas,
        overlays_ab=ov_ab,
        overlays_ba=ov_ba,
        cross_ab=cross_aspects(a, b),
        cross_ba=cross_aspects(b, a),
        sync=sync,
        ledger=led.items,
        navamsa_note=(
            "The navamsa (D9) is the division classical practice reads for "
            "marriage and inner disposition, so it is weighed alongside the "
            "rasi rather than after it."
        ),
    )

    for topic, description in topics.items():
        items = led.for_topic(topic)
        outcome = run_gate(items)
        result = TopicResult(topic=topic, description=description, outcome=outcome, evidence=items)
        (report.findings if outcome.passed else report.withheld).append(result)

    return report


@dataclass
class GroupReport:
    """Pairwise comparison across three or more people."""

    labels: list[str]
    mode: str
    pairs: list[PairReport]

    def pair(self, a: str, b: str) -> PairReport | None:
        for p in self.pairs:
            if {p.a, p.b} == {a, b}:
                return p
        return None

    @property
    def matrix(self) -> dict[tuple[str, str], float]:
        """Koota totals as a lookup, for rendering a grid."""
        return {(p.a, p.b): p.milan.total for p in self.pairs}


def compare_group(people: list[Person], now_jd: float, mode: str = "friendship") -> GroupReport:
    """Every pair among three or more people.

    Deliberately pairwise. There is no classical method for scoring a group as
    a whole, and inventing one would be exactly the kind of thing this codebase
    refuses to do elsewhere.
    """
    if len(people) < 2:
        raise ValueError("Need at least two people to compare.")
    pairs: list[PairReport] = []
    for i, first in enumerate(people):
        for second in people[i + 1 :]:
            pairs.append(compare(first, second, now_jd, mode))
    return GroupReport(labels=[p.label for p in people], mode=mode, pairs=pairs)


def _ord(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"


def _and_join(items: list[str]) -> str:
    if not items:
        return "nothing"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]
