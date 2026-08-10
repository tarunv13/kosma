"""What a graha does in a bhava: meaning, strengths, weaknesses, temperament, remedy.

The classical texts give results for each planet in each house -- BPHS spends
chapters 24 to 33 on exactly this, and Phaladeepika chapters 7 and 8 restate it
more compactly. That is 108 combinations, and the honest way to carry them is
not 108 hand-written paragraphs pretending to be independent judgements.

It is built compositionally instead, from four things the tradition actually
distinguishes:

* **The graha's own nature.** Saturn constrains, delays and endures wherever it
  falls. That does not change with the house.
* **The bhava's domain.** The house says *what* is being constrained.
* **The house's class.** Kendra, trikona, dusthana and upachaya each modify the
  result in a way the texts are explicit about -- a malefic in an upachaya
  improves with time; the same malefic in a kendra does not.
* **The planet's actual dignity in this chart.** This is the part a lookup
  table cannot do. Exalted Saturn in the 7th and debilitated Saturn in the 7th
  are not the same placement, and text that reads identically for both is
  decoration rather than astrology.

The strengths and weaknesses are therefore genuinely per-chart. What is *not*
generated is a prediction: this module says what the tradition holds a
placement to signify, and the gate in :mod:`kosma.evidence` remains the only
thing that decides what may be asserted about a life.

Remedies are attached to the graha, never to the combination. There is a
well-attested register of mantra, daana and vara per planet; there is no
canonical remedy for "Mars in the 7th", and inventing one would be the exact
failure this project exists to avoid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .interpretations import HOUSE_GOVERNS

# ── The nine grahas, in their own right ───────────────────────────────


@dataclass(frozen=True)
class GrahaNature:
    sanskrit: str
    """The classical name."""
    signifies: str
    """What this planet stands for in any chart."""
    temperament: str
    """What it does to the character of whatever it touches."""
    when_strong: str
    """What a well-placed instance of it gives."""
    when_weak: str
    """What a poorly-placed instance of it costs."""
    nature_note: str
    """How it colours the person themselves."""
    mantra: str
    transliteration: str
    gem: str
    daana: str
    vara: str
    practical: str
    """A remedy that is behavioural rather than transactional."""


GRAHAS: dict[str, GrahaNature] = {
    "Sun": GrahaNature(
        sanskrit="Surya",
        signifies="the father, authority, vitality, the self that is seen and judged",
        temperament="illuminates and exposes; burns what sits too close to it",
        when_strong="steadiness of purpose, natural authority, and a spine that holds under scrutiny",
        when_weak="a brittle sense of standing, trouble with authority, or health that follows morale",
        nature_note=(
            "gives a person who needs to be recognised for what they actually "
            "did, and who takes being overlooked harder than being opposed"
        ),
        mantra="ॐ घृणिः सूर्याय नमः",
        transliteration="Om Ghrini Suryaya Namah",
        gem="Ruby (manikya)",
        daana="wheat, jaggery, copper",
        vara="Sunday",
        practical=(
            "Sunrise light on the face, and one thing finished properly before "
            "the day fills up. Surya rules the beginning of things; a day that "
            "starts in reaction rarely recovers its authorship."
        ),
    ),
    "Moon": GrahaNature(
        sanskrit="Chandra",
        signifies="the mother, the mind, memory, the public, and what a person needs to feel safe",
        temperament="reflects and fluctuates; takes the colour of whatever it sits with",
        when_strong="an even temper, easy rapport, and a mind that settles quickly after disturbance",
        when_weak="moods that run the day, restless sleep, and comfort sought where it is not found",
        nature_note=(
            "gives someone whose competence genuinely varies with how safe they "
            "feel, which others often misread as inconsistency"
        ),
        mantra="ॐ सों सोमाय नमः",
        transliteration="Om Som Somaya Namah",
        gem="Pearl (mukta)",
        daana="rice, milk, silver",
        vara="Monday",
        practical=(
            "Protect sleep and water before anything else, and keep one "
            "relationship where nothing has to be performed. The Moon is the "
            "manas; it repairs through rest and safety, not through effort."
        ),
    ),
    "Mars": GrahaNature(
        sanskrit="Mangala",
        signifies="courage, younger siblings, land, machinery, surgery, and the will to force a matter",
        temperament="cuts, separates and accelerates; makes things happen and makes them break",
        when_strong="decisiveness, physical courage, and the ability to finish what confrontation starts",
        when_weak="temper that costs more than it wins, accidents, and conflict entered without an exit",
        nature_note=(
            "gives a person who would rather have a hard conversation than a "
            "long ambiguity, and who mistakes patience for defeat"
        ),
        mantra="ॐ अं अङ्गारकाय नमः",
        transliteration="Om Am Angarakaya Namah",
        gem="Red coral (moonga)",
        daana="red lentils, copper",
        vara="Tuesday",
        practical=(
            "Spend the heat deliberately -- hard physical training, early in the "
            "day. Mangala's difficulty is never the energy itself, only its "
            "arriving with nowhere to go."
        ),
    ),
    "Mercury": GrahaNature(
        sanskrit="Budha",
        signifies="speech, commerce, analysis, documents, and the intelligence that handles detail",
        temperament="divides, compares and communicates; neutral, and takes on its company's character",
        when_strong="quick understanding, persuasive speech, and skill with anything that must be exact",
        when_weak="cleverness without judgement, nervous overthinking, and agreements that read badly later",
        nature_note=(
            "gives someone who can argue any side well, and who has to watch "
            "that facility does not stand in for actually deciding"
        ),
        mantra="ॐ बुं बुधाय नमः",
        transliteration="Om Bum Budhaya Namah",
        gem="Emerald (panna)",
        daana="green gram, books",
        vara="Wednesday",
        practical=(
            "Write the thing down before saying it, and read contracts twice. "
            "Budha rules the gap between what was meant and what was recorded."
        ),
    ),
    "Jupiter": GrahaNature(
        sanskrit="Brihaspati",
        signifies="teachers, children, wealth, dharma, and counsel worth taking",
        temperament="expands and protects whatever it touches, for better and for worse",
        when_strong="good judgement, genuine generosity, and help arriving from people who need not have offered",
        when_weak="excess, misplaced faith, and advice given more freely than it is earned",
        nature_note=(
            "gives a person others come to for judgement, and whose main risk "
            "is believing their own expansiveness"
        ),
        mantra="ॐ बृं बृहस्पतये नमः",
        transliteration="Om Brim Brihaspataye Namah",
        gem="Yellow sapphire (pukhraj)",
        daana="turmeric, chana dal, saffron",
        vara="Thursday",
        practical=(
            "Teach something, and keep a teacher. Guru's grace in the classical "
            "reading moves through the act of transmission, in both directions."
        ),
    ),
    "Venus": GrahaNature(
        sanskrit="Shukra",
        signifies="marriage, pleasure, art, vehicles, comfort, and the capacity to value things",
        temperament="attracts, harmonises and softens; seeks the agreeable over the true",
        when_strong="charm that opens doors, real aesthetic judgement, and ease in partnership",
        when_weak="indulgence, avoidance of necessary conflict, and taste standing in for discernment",
        nature_note=(
            "gives someone who reads a room instantly and will hold a false "
            "peace longer than is good for them"
        ),
        mantra="ॐ शुं शुक्राय नमः",
        transliteration="Om Shum Shukraya Namah",
        gem="Diamond (heera)",
        daana="white cloth, curd, rice",
        vara="Friday",
        practical=(
            "Make something with your hands rather than only consuming what "
            "others made. Shukra sours when appetite outruns creation."
        ),
    ),
    "Saturn": GrahaNature(
        sanskrit="Shani",
        signifies="time, labour, the poor and the old, discipline, and what must be endured",
        temperament="delays, constricts and tests; gives late, and gives permanently",
        when_strong="endurance, realism, and the rare ability to keep working with no visible reward",
        when_weak="chronic delay, isolation, and a heaviness that reads to others as pessimism",
        nature_note=(
            "gives a person who matures late and then does not regress, and who "
            "carries an early sense that nothing arrives unearned"
        ),
        mantra="ॐ शं शनैश्चराय नमः",
        transliteration="Om Sham Shanaishcharaya Namah",
        gem="Blue sapphire (neelam)",
        daana="sesame, black cloth, iron",
        vara="Saturday",
        practical=(
            "Serve someone with less than you, without it being seen. Shani is "
            "the karaka of labour and of the overlooked, and the classical "
            "remedy is consistently to take their side."
        ),
    ),
    "Rahu": GrahaNature(
        sanskrit="Rahu",
        signifies="obsession, foreign things, technology, ambition without precedent, and sudden rise",
        temperament="amplifies and distorts; gives the appearance of a thing before its substance",
        when_strong="unconventional advantage, and success in what has no established path",
        when_weak="fixation, reputation built ahead of capacity, and gain that does not survive scrutiny",
        nature_note=(
            "gives hunger that is real and a satisfaction that is not; the "
            "wanting is genuine and the arriving keeps moving"
        ),
        mantra="ॐ रां राहवे नमः",
        transliteration="Om Ram Rahave Namah",
        gem="Hessonite (gomed)",
        daana="sesame, blankets",
        vara="Saturday",
        practical=(
            "Name the thing being chased out loud, to someone who will push "
            "back. Rahu's damage is done in private, where the story is never "
            "contradicted."
        ),
    ),
    "Ketu": GrahaNature(
        sanskrit="Ketu",
        signifies="detachment, past attainment, moksha, and the area a person is finished with",
        temperament="dissolves and withdraws; removes interest rather than opportunity",
        when_strong="penetrating insight, indifference to what others are trapped by, and real spiritual capacity",
        when_weak="disengagement from what still needs tending, and skill dropped for want of caring",
        nature_note=(
            "gives someone already competent where they feel least invested, "
            "and puzzled that others find it difficult"
        ),
        mantra="ॐ कें केतवे नमः",
        transliteration="Om Kem Ketave Namah",
        gem="Cat's eye (lehsunia)",
        daana="sesame, blankets",
        vara="Tuesday",
        practical=(
            "Keep a practice with no outcome attached. Ketu is the only graha "
            "that improves when nothing is being pursued through it."
        ),
    ),
}

REMEDY_CAVEAT = (
    "Classical associations for this graha, not a prescription for this "
    "placement. The register of mantra, daana and vara is attested per planet; "
    "no canonical remedy exists per planet-in-house, so none is invented here."
)

RATNA_CAVEAT = (
    "Gemstones especially: most practitioners hold that ratna requires a full "
    "reading of the whole chart rather than a lookup by planet, and a wrongly "
    "chosen stone is held to do harm. Treat this as reference, not instruction."
)

# ── House classes, which the texts treat differently ──────────────────

KENDRA = (1, 4, 7, 10)
TRIKONA = (1, 5, 9)
DUSTHANA = (6, 8, 12)
UPACHAYA = (3, 6, 10, 11)

_CLASS_NOTE: dict[str, str] = {
    "kendra": (
        "This is an angular house (kendra) -- one of the four the chart is "
        "built on. Whatever sits here acts visibly and structurally, so its "
        "quality matters more than it would elsewhere."
    ),
    "trikona": (
        "This is a trine (trikona), classically the most fortunate group of "
        "houses. Placements here tend to be supported rather than obstructed."
    ),
    "dusthana": (
        "This is one of the difficult houses (dusthana: 6, 8, 12), tied to "
        "debt, crisis and loss. A benefic here is partly spent; a malefic here "
        "is often more at home than it looks, because it has something to "
        "fight."
    ),
    "upachaya": (
        "This is a growing house (upachaya). The classical rule is that these "
        "improve with time and effort, and that malefics do well in them -- "
        "difficulty here is the kind that yields to work."
    ),
}


def house_classes(house: int) -> tuple[str, ...]:
    out = []
    if house in KENDRA:
        out.append("kendra")
    if house in TRIKONA:
        out.append("trikona")
    if house in DUSTHANA:
        out.append("dusthana")
    if house in UPACHAYA:
        out.append("upachaya")
    return tuple(out)


# ── Placements the texts single out by name ───────────────────────────
#
# Only where a classical source says something specific that composition
# would not produce. Everything else is left to compose, rather than padded
# with invented particulars.

NOTABLE: dict[tuple[str, int], str] = {
    (
        "Sun",
        10,
    ): "Parashara treats the Sun in the 10th as directly strengthened. It gains dig bala (directional strength) here, and the house of action is its natural ground.",
    (
        "Sun",
        1,
    ): "The Sun in the ascendant gives the chart its temperament directly: the self and the significator of self occupy the same house.",
    (
        "Moon",
        4,
    ): "The Moon in the 4th is in its own natural house: the karaka of the mother and of inner ground, sitting in the bhava of both.",
    (
        "Moon",
        10,
    ): "The Moon in the 10th gains dig bala. Public life suits it, and public life also exposes its fluctuation.",
    (
        "Mars",
        7,
    ): "Mars in the 7th is one of the classical Mangal (kuja) dosha positions, held to press on marriage through friction rather than absence.",
    (
        "Mars",
        1,
    ): "Mars in the ascendant is a Mangal dosha position, and gives the body and temperament its edge directly.",
    (
        "Mars",
        8,
    ): "Mars in the 8th is a Mangal dosha position and touches longevity and crisis; the classical advice is to spend its force deliberately.",
    (
        "Mars",
        3,
    ): "Mars in the 3rd is at its most useful, giving courage and initiative in the house of exactly those, and an upachaya besides.",
    (
        "Mercury",
        1,
    ): "Mercury in the ascendant gives the intelligence a verbal, analytical cast that shows in how the person first presents.",
    (
        "Mercury",
        10,
    ): "Mercury in the 10th gains dig bala; work involving speech, writing or figures is favoured.",
    (
        "Jupiter",
        1,
    ): "Jupiter in the ascendant gains dig bala and is among the most protective single placements in the classical literature.",
    (
        "Jupiter",
        5,
    ): "Jupiter in the 5th sits in the house of children and merit as their natural significator, which the texts read warmly.",
    (
        "Jupiter",
        6,
    ): "Jupiter in the 6th is a benefic in a dusthana: its expansiveness is spent on debt, illness and enemies rather than on growth.",
    (
        "Venus",
        7,
    ): "Venus in the 7th is the karaka of marriage in the house of marriage. Classical opinion is divided on whether a karaka in its own bhava helps or overloads it.",
    (
        "Venus",
        4,
    ): "Venus in the 4th gains dig bala: comfort, vehicles and the pleasantness of home are favoured.",
    (
        "Venus",
        12,
    ): "Venus in the 12th is read as strong for the pleasures of the 12th, meaning seclusion and foreign places, and weak for anything requiring restraint.",
    (
        "Saturn",
        7,
    ): "Saturn in the 7th gains dig bala and delays partnership rather than denying it; what forms late, in this reading, forms durably.",
    (
        "Saturn",
        1,
    ): "Saturn in the ascendant is a heavy placement for the body and early temperament, and among the most reliably maturing ones.",
    (
        "Saturn",
        3,
    ): "Saturn in the 3rd is an upachaya placement: courage arrives through repetition rather than by temperament.",
    (
        "Saturn",
        6,
    ): "Saturn in the 6th is a malefic in a dusthana, which the texts read as genuinely good: it is well suited to grinding down debt, illness and opposition.",
    (
        "Saturn",
        10,
    ): "Saturn in the 10th gains dig bala. Career is slow, self-built, and rarely lost once established.",
    (
        "Rahu",
        3,
    ): "Rahu in the 3rd is among its better placements: an upachaya where unconventional ambition converts into actual initiative.",
    (
        "Rahu",
        6,
    ): "Rahu in the 6th is classically strong because it fights, and here there is something to fight.",
    (
        "Rahu",
        11,
    ): "Rahu in the 11th is read as favourable for gain, with the standing caution that the gain outpaces the ability to hold it.",
    (
        "Ketu",
        12,
    ): "Ketu in the 12th is its most classically favourable position: the karaka of release, in the house of it.",
    (
        "Ketu",
        9,
    ): "Ketu in the 9th complicates inherited belief, because the tradition given is rarely the one kept.",
}


@dataclass(frozen=True)
class PlacementReading:
    planet: str
    sanskrit: str
    house: int
    sign: str
    dignity: str
    classes: tuple[str, ...]
    signifies: str
    """What this planet does in this house."""
    strengths: str
    weaknesses: str
    nature: str
    """How it colours the person."""
    class_note: str
    notable: str
    """A classical particular, where one exists."""
    condition: str
    """What this chart's dignity, retrogression and combustion do to the above."""
    remedy: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "planet": self.planet,
            "sanskrit": self.sanskrit,
            "house": self.house,
            "sign": self.sign,
            "dignity": self.dignity,
            "classes": list(self.classes),
            "signifies": self.signifies,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "nature": self.nature,
            "class_note": self.class_note,
            "notable": self.notable,
            "condition": self.condition,
            "remedy": self.remedy,
        }


# Dignity -> how much to trust the strong reading over the weak one.
_STRONG = {"exalted", "moolatrikona", "own sign", "swakshetra", "great friend", "friend"}
_WEAK = {"debilitated", "great enemy", "enemy"}


def _dignity_phrase(planet: str, dignity: str) -> str:
    """Read a dignity state into a sentence.

    The engine states these as noun phrases -- "own sign", "enemy's sign",
    "neutral sign" -- which slot straight into a table but produce "Sun is
    neutral sign" in prose. They need the preposition and article the table
    left out. Anything ending in "sign" is a placement; the rest ("exalted",
    "debilitated", "moolatrikona") are already adjectival.
    """
    d = dignity.lower().strip()
    if d in {"own sign", "swakshetra"}:
        return f"{planet} is in its own sign"
    if d.startswith("moolatrikona"):
        return f"{planet} is in its moolatrikona"
    if d.endswith("sign"):
        article = "an" if d[0] in "aeiou" else "a"
        return f"{planet} sits in {article} {d}"
    return f"{planet} is {d}"


def _condition_sentence(
    planet: str, dignity: str, retrograde: bool, combust: bool, house: int
) -> str:
    """What this chart does to the general reading.

    A placement table that reads the same for an exalted planet and a
    debilitated one is decoration. This is the sentence that makes the entry
    about this chart rather than about the abstract combination.
    """
    d = dignity.lower()
    parts: list[str] = []

    phrase = _dignity_phrase(planet, dignity)
    if any(k in d for k in _STRONG):
        parts.append(
            f"In this chart {phrase}, so the strengths above are the part to "
            f"weight and the weaknesses are the milder risk."
        )
    elif any(k in d for k in _WEAK):
        parts.append(
            f"In this chart {phrase}, so the weaknesses above are the live "
            f"ones and the strengths have to be worked for rather than assumed."
        )
    else:
        parts.append(
            f"In this chart {phrase}, neither reinforced nor undermined by "
            f"the sign, so the house matters more than the dignity does here."
        )

    if retrograde:
        parts.append(
            "It is retrograde, which classical practice reads as the matter "
            "turning inward: strong, but expressed on its own terms and often "
            "revisited rather than settled once."
        )
    if combust:
        parts.append(
            "It is combust, meaning too close to the Sun to be seen, which the texts "
            "treat as weakening its independent expression, whatever its "
            "dignity otherwise."
        )
    if house in DUSTHANA and planet in ("Jupiter", "Venus", "Moon", "Mercury"):
        parts.append(
            "A benefic in a difficult house is partly consumed by it: the good "
            "it does tends to be repair rather than gain."
        )
    return " ".join(parts)


def placement_reading(
    planet: str,
    house: int,
    sign: str,
    dignity: str,
    *,
    retrograde: bool = False,
    combust: bool = False,
) -> PlacementReading:
    """Everything the tradition says about one graha in one bhava, for this chart."""
    nature = GRAHAS[planet]
    domain = HOUSE_GOVERNS[house]
    classes = house_classes(house)

    # The first clause of the house's domain, used to keep sentences readable.
    short_domain = domain.split(",")[0].split(".")[0].strip().lower()

    signifies = (
        f"{nature.sanskrit} ({planet}) signifies {nature.signifies}. Placed in "
        f"the {_ordinal(house)} house, it brings that to bear on "
        f"{short_domain}. Its way of working there: it {nature.temperament}."
    )

    strengths = f"Well placed, it gives {nature.when_strong}, applied to {short_domain}."
    weaknesses = f"Poorly placed, it costs {nature.when_weak}, felt through {short_domain}."

    class_note = " ".join(_CLASS_NOTE[c] for c in classes) if classes else ""

    return PlacementReading(
        planet=planet,
        sanskrit=nature.sanskrit,
        house=house,
        sign=sign,
        dignity=dignity,
        classes=classes,
        signifies=signifies,
        strengths=strengths,
        weaknesses=weaknesses,
        nature=f"On the person: it {nature.nature_note}.",
        class_note=class_note,
        notable=NOTABLE.get((planet, house), ""),
        condition=_condition_sentence(planet, dignity, retrograde, combust, house),
        remedy={
            "graha": nature.sanskrit,
            "mantra": nature.mantra,
            "transliteration": nature.transliteration,
            "gem": nature.gem,
            "daana": nature.daana,
            "vara": nature.vara,
            "practical": nature.practical,
            "caveat": REMEDY_CAVEAT,
            "ratna_caveat": RATNA_CAVEAT,
        },
    )


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
