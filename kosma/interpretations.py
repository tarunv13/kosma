"""
Static interpretation lookups for the Soul Blueprint PDF.

These are concise, classically grounded descriptions used to render the
report. They are intentionally brief and neutral; the engine produces the
exact placements and the report cross-references them with these notes.
"""

# ── House significations ──────────────────────────────────────────────

HOUSE_THEMES: dict[int, str] = {
    1: "Self, body, vitality, life direction, the way you arrive in any room.",
    2: "Speech, accumulated wealth, family of origin, food, voice, values.",
    3: "Courage, siblings, short journeys, hands, communication, willpower.",
    4: "Mother, home, emotional foundations, vehicles, real estate, inner peace.",
    5: "Children, creativity, intelligence, romance, prior-life merit, speculation.",
    6: "Service, debts, illness, daily work, enemies, discipline, recovery.",
    7: "Marriage, partners, public dealings, contracts, the mirror you choose.",
    8: "Hidden things, transformation, inheritance, occult, longevity, crises.",
    9: "Dharma, father, gurus, long journeys, philosophy, fortune, higher learning.",
    10: "Career, public reputation, authority, action in the world, the throne.",
    11: "Income, gains, networks, elder siblings, fulfilment of desires.",
    12: "Loss, exile, foreign lands, sleep, liberation, the unconscious.",
}


# ── Ascendant character (12 rising signs) ─────────────────────────────

ASCENDANTS: dict[str, str] = {
    "Aries": (
        "Mars rising. You arrive with momentum and a forward lean. Direct, "
        "physical, impatient with theatre. Identity is forged by initiating, "
        "not finishing. The work is learning to slow down without losing edge."
    ),
    "Taurus": (
        "Venus rising. Sensual, steady, fond of comfort and beauty. You move "
        "slowly until you are sure, then refuse to be moved. Identity is built "
        "by what you accumulate and tend. The work is releasing what you have "
        "outgrown."
    ),
    "Gemini": (
        "Mercury rising. Curious, verbal, plural. You are several people at "
        "once and that is the gift. Identity rides on language and connection. "
        "The work is choosing depth over restless variety."
    ),
    "Cancer": (
        "Moon rising. You take on the weather of every room you enter. Tender, "
        "protective, emotionally porous. Identity is bound to home, lineage and "
        "memory. The work is building a self that does not depend on being needed."
    ),
    "Leo": (
        "Sun rising. You are visible whether you mean to be or not. Generous, "
        "performative, stubborn about dignity. Identity is sovereignty itself. "
        "The work is leading without needing applause."
    ),
    "Virgo": (
        "Mercury rising in an earth sign. Analytical, careful, devoted to skill. "
        "Identity is forged through service and craft. The work is permitting "
        "imperfection without collapsing self-worth."
    ),
    "Libra": (
        "Venus rising in an air sign. Diplomatic, aesthetic, allergic to crude "
        "behaviour. Identity is built in relationship. The work is choosing your "
        "own preferences over the consensus you negotiate."
    ),
    "Scorpio": (
        "Mars rising in a water sign. Penetrating, magnetic, private. You see "
        "what others paper over. Identity is forged through cycles of death and "
        "rebirth. The work is trusting before you have control."
    ),
    "Sagittarius": (
        "Jupiter rising. Philosophical, generous, restless for meaning. You need "
        "horizon. Identity is found on the road and in teachers. The work is "
        "finishing what you started before chasing the next vision."
    ),
    "Capricorn": (
        "Saturn rising. Mature beyond your years, structural, slow-burn. "
        "Identity is what you build over time. The work is allowing tenderness "
        "without seeing it as weakness."
    ),
    "Aquarius": (
        "Saturn rising in an air sign. Detached, systemic, oddly humane. You see "
        "patterns where others see people. Identity is the shape of your ideals. "
        "The work is letting individuals matter as much as the cause."
    ),
    "Pisces": (
        "Jupiter rising in a water sign. Dreamy, devotional, boundary-poor. You "
        "absorb what is around you. Identity is the membrane between worlds. "
        "The work is staying embodied while remaining open."
    ),
}


# ── Sun in signs (ego, father, public self) ───────────────────────────

SUN_IN_SIGN: dict[str, str] = {
    "Aries": "The will is direct and combative. You lead, or chafe under leadership.",
    "Taurus": "The will is steady and sensual. You build slowly and resent being rushed.",
    "Gemini": "The will moves through ideas and words. You change shape often.",
    "Cancer": "The will is moody, protective, family-bound. The Sun is a guest here, less at home.",
    "Leo": "The will is sovereign. You require dignity and a stage of some kind.",
    "Virgo": "The will refines. You measure yourself against precision and usefulness.",
    "Libra": "The Sun is debilitated. The ego is softened, sometimes dissolved into others. Strength is built by choosing.",
    "Scorpio": "The will is concentrated and private. You do not show your hand.",
    "Sagittarius": "The will is expansive, philosophical, teacher-shaped.",
    "Capricorn": "The will is austere and ambitious. Authority is the lesson.",
    "Aquarius": "The will is reformist. You lead by deviating from convention.",
    "Pisces": "The will is dissolved in service or art. You shine when you surrender ego.",
}


# ── Moon in signs (emotional architecture) ────────────────────────────

MOON_IN_SIGN: dict[str, str] = {
    "Aries": "Emotionally restless and reactive. Feelings move like fire and pass quickly.",
    "Taurus": "Moon is exalted. Emotions are rich, sensual, slow to start, slow to leave.",
    "Gemini": "Emotional life is verbal. You think your feelings before you feel them.",
    "Cancer": "Moon is at home. Deeply feeling, lineage-aware, easily wounded and easily healed.",
    "Leo": "Emotional life seeks recognition. You feel most alive when seen.",
    "Virgo": "Emotional life filters through analysis. You self-correct rather than soothe.",
    "Libra": "Emotional life mirrors others. You feel most yourself in dialogue.",
    "Scorpio": "Moon is debilitated. Feelings run deep and dark; healing requires excavation.",
    "Sagittarius": "Emotional life moves toward meaning, travel, teachers.",
    "Capricorn": "Emotional life is contained, responsible, slow to trust.",
    "Aquarius": "Emotional life is detached and ideological. You love at a distance.",
    "Pisces": "Emotional life is oceanic. You dissolve into what surrounds you.",
}


# ── Other planet-in-sign quick lines ──────────────────────────────────

MARS_IN_SIGN: dict[str, str] = {
    "Aries": "Action is direct, raw, fast. Anger is honest.",
    "Taurus": "Action is slow, persistent, possessive. Anger smoulders.",
    "Gemini": "Action is verbal and scattered. Energy goes to argument.",
    "Cancer": "Mars debilitated. Action is moody, indirect, defensive.",
    "Leo": "Action is theatrical and proud. You fight for dignity.",
    "Virgo": "Action is precise, critical, work-driven.",
    "Libra": "Action is diplomatic until pushed; then surgical.",
    "Scorpio": "Action is strategic, secretive, all-or-nothing.",
    "Sagittarius": "Action is philosophical, idealistic, restless.",
    "Capricorn": "Mars exalted. Action is disciplined, ambitious, mature.",
    "Aquarius": "Action is reformist, oddly impersonal.",
    "Pisces": "Action is intuitive, devotional, easily diffused.",
}

VENUS_IN_SIGN: dict[str, str] = {
    "Aries": "Love is hot, impatient, direct.",
    "Taurus": "Venus at home. Love is sensual, loyal, slow-burning.",
    "Gemini": "Love is conversational, plural, easily distracted.",
    "Cancer": "Love is nurturing, protective, family-shaped.",
    "Leo": "Love is dramatic, generous, demands devotion.",
    "Virgo": "Venus debilitated. Love is critical, service-shaped, perfectionist.",
    "Libra": "Venus at home. Love is aesthetic, fair, partnership-driven.",
    "Scorpio": "Love is intense, jealous, transformative.",
    "Sagittarius": "Love seeks meaning, travel, freedom.",
    "Capricorn": "Love is committed, slow, status-aware.",
    "Aquarius": "Love is unconventional, friendship-first.",
    "Pisces": "Venus exalted. Love is devotional, dissolving, transcendent.",
}

MERCURY_IN_SIGN: dict[str, str] = {
    "Aries": "Quick, blunt, argumentative speech.",
    "Taurus": "Slow, deliberate, sensory speech.",
    "Gemini": "Mercury at home. Brilliant, plural, verbal.",
    "Cancer": "Speech is emotional, memory-laden.",
    "Leo": "Speech is performative, declarative.",
    "Virgo": "Mercury at home and exalted. Precise, analytical, editorial.",
    "Libra": "Speech is diplomatic, balancing.",
    "Scorpio": "Speech is incisive, secretive, surgical.",
    "Sagittarius": "Mercury debilitated. Speech is grand, sometimes unfocused.",
    "Capricorn": "Speech is cautious, structural, dry.",
    "Aquarius": "Speech is systemic, contrarian.",
    "Pisces": "Mercury debilitated. Speech is poetic, oblique.",
}

JUPITER_IN_SIGN: dict[str, str] = {
    "Aries": "Faith is direct and pioneering.",
    "Taurus": "Faith is grounded in beauty and resources.",
    "Gemini": "Faith is intellectual and plural.",
    "Cancer": "Jupiter exalted. Faith is rooted in family, mother, home.",
    "Leo": "Faith is regal, dharma seen as sovereign duty.",
    "Virgo": "Faith is service-oriented, sometimes critical.",
    "Libra": "Faith is partnership-shaped and aesthetic.",
    "Scorpio": "Faith comes through transformation and crisis.",
    "Sagittarius": "Jupiter at home. Faith is philosophical, expansive.",
    "Capricorn": "Jupiter debilitated. Faith is austere, doubt-ridden, slowly earned.",
    "Aquarius": "Faith is reformist and humane.",
    "Pisces": "Jupiter at home. Faith is devotional, mystical.",
}

SATURN_IN_SIGN: dict[str, str] = {
    "Aries": "Saturn debilitated. Authority and patience are the lesson; impulse the cost.",
    "Taurus": "Saturn rewards endurance with stability.",
    "Gemini": "Saturn structures speech and learning.",
    "Cancer": "Saturn restricts emotional flow. Mother karma surfaces.",
    "Leo": "Saturn challenges ego; humility is the gift.",
    "Virgo": "Saturn rewards craft, discipline, service.",
    "Libra": "Saturn exalted. Authority through fairness; partnerships are the path.",
    "Scorpio": "Saturn deepens through crisis and transformation.",
    "Sagittarius": "Saturn structures faith, often through doubt.",
    "Capricorn": "Saturn at home. Mature, patient, ambitious.",
    "Aquarius": "Saturn at home. Reformist, systemic, slow-built.",
    "Pisces": "Saturn dissolves boundaries; spiritual discipline is the gift.",
}

RAHU_IN_SIGN: dict[str, str] = {
    "Aries": "Hunger for selfhood and direct action.",
    "Taurus": "Hunger for security, beauty, sensual mastery.",
    "Gemini": "Hunger for words, networks, multiplicity.",
    "Cancer": "Hunger for family, roots, emotional belonging.",
    "Leo": "Hunger for recognition and sovereignty.",
    "Virgo": "Hunger for skill, precision, indispensability.",
    "Libra": "Hunger for partnership, aesthetics, fairness.",
    "Scorpio": "Hunger for transformation, taboo knowledge, intensity.",
    "Sagittarius": "Hunger for meaning, travel, teachers.",
    "Capricorn": "Hunger for authority, structure, legacy.",
    "Aquarius": "Hunger for influence, ideology, the future.",
    "Pisces": "Hunger for transcendence, dissolution, art.",
}

KETU_IN_SIGN: dict[str, str] = {
    "Aries": "Past mastery of action; this life calls for measured response.",
    "Taurus": "Past mastery of sensual security; this life calls for letting go.",
    "Gemini": "Past mastery of words; this life calls for direct experience.",
    "Cancer": "Past mastery of nurture; this life calls for boundaries.",
    "Leo": "Past mastery of sovereignty; this life calls for humility.",
    "Virgo": "Past mastery of skill; this life calls for trust.",
    "Libra": "Past mastery of relationship; this life calls for self-defined choice.",
    "Scorpio": "Past mastery of intensity; this life calls for steady ground.",
    "Sagittarius": "Past mastery of teaching; this life calls for listening.",
    "Capricorn": "Past mastery of authority; this life calls for surrender.",
    "Aquarius": "Past mastery of ideology; this life calls for personal warmth.",
    "Pisces": "Past mastery of mysticism; this life calls for embodiment.",
}


PLANET_IN_SIGN: dict[str, dict[str, str]] = {
    "Sun": SUN_IN_SIGN,
    "Moon": MOON_IN_SIGN,
    "Mars": MARS_IN_SIGN,
    "Mercury": MERCURY_IN_SIGN,
    "Jupiter": JUPITER_IN_SIGN,
    "Venus": VENUS_IN_SIGN,
    "Saturn": SATURN_IN_SIGN,
    "Rahu": RAHU_IN_SIGN,
    "Ketu": KETU_IN_SIGN,
}


# ── Mahadasha (current life chapter) ──────────────────────────────────

MAHADASHA: dict[str, str] = {
    "Sun": (
        "Sun mahadasha (6 years). A chapter of will, authority, visibility. "
        "Themes: father, recognition, vital force, soul-purpose. Lessons: "
        "leadership without ego inflation."
    ),
    "Moon": (
        "Moon mahadasha (10 years). A chapter of feeling, public, mother, home. "
        "Themes: emotional cycles, family, the inner life. Lessons: steady the "
        "tide without numbing it."
    ),
    "Mars": (
        "Mars mahadasha (7 years). A chapter of action, courage, conflict. "
        "Themes: siblings, drive, accidents, decisive moves. Lessons: precision "
        "over aggression."
    ),
    "Mercury": (
        "Mercury mahadasha (17 years). A chapter of intellect, communication, "
        "commerce, learning. Themes: books, contracts, networks, skill. Lessons: "
        "depth before scattering."
    ),
    "Jupiter": (
        "Jupiter mahadasha (16 years). A chapter of expansion, dharma, "
        "teachers, children. Themes: meaning, abundance, faith, children. "
        "Lessons: discernment within optimism."
    ),
    "Venus": (
        "Venus mahadasha (20 years). A chapter of love, beauty, comfort, "
        "marriage, art. Themes: relationships, aesthetics, vehicles, women. "
        "Lessons: sweetness without bondage."
    ),
    "Saturn": (
        "Saturn mahadasha (19 years). A chapter of structure, karma, slow "
        "fruit. Themes: work, elders, discipline, delay. Lessons: patience as "
        "alchemy."
    ),
    "Rahu": (
        "Rahu mahadasha (18 years). A chapter of obsession, hunger, foreign "
        "currents. Themes: ambition, taboo, sudden rise. Lessons: do not let the "
        "smoke choose for you."
    ),
    "Ketu": (
        "Ketu mahadasha (7 years). A chapter of detachment, dissolution, "
        "moksha-orientation. Themes: loss as initiation, the spiritual axis. "
        "Lessons: release without bitterness."
    ),
}


# ── Karaka roles ──────────────────────────────────────────────────────

KARAKA_BLURB: dict[str, str] = {
    "Atmakaraka": "The soul-significator. The planet with the highest degree "
    "represents the innermost agenda of this lifetime.",
    "Amatyakaraka": "Career, ministers, advisors. How you act on the soul's agenda in the world.",
    "Bhratrukaraka": "Siblings, courage, short journeys.",
    "Matrukaraka": "Mother, emotional foundation, home.",
    "Putrakaraka": "Children, creativity, prior merit.",
    "Gnatikaraka": "Adversaries, cousins, hidden enemies, illness.",
    "Darakaraka": "Spouse-significator. The flavour of the partner the soul draws toward itself.",
}


# ── Helpers ───────────────────────────────────────────────────────────


def planet_in_sign(planet: str, sign: str) -> str:
    return PLANET_IN_SIGN.get(planet, {}).get(sign, "")


def planet_in_house_brief(planet: str, house: int) -> str:
    """Combine planet character with house theme into a single brief line."""
    theme = HOUSE_THEMES.get(house, "")
    return f"{planet} colours the {ordinal(house)} house: {theme}"


def ordinal(n: int) -> str:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"


# ── Bhava karakas (natural significators) ─────────────────────────────
#
# The graha that signifies a house irrespective of who rules or occupies it.
# BPHS assigns one principal karaka per bhava; where later authors commonly
# add a second, it is noted rather than silently merged.

BHAVA_KARAKA: dict[int, str] = {
    1: "Sun",
    2: "Jupiter",
    3: "Mars",
    4: "Moon",
    5: "Jupiter",
    6: "Mars",
    7: "Venus",
    8: "Saturn",
    9: "Jupiter",
    10: "Mercury",
    11: "Jupiter",
    12: "Saturn",
}

BHAVA_KARAKA_NOTE: dict[int, str] = {
    1: "Sun signifies the body and the self.",
    2: "Jupiter signifies accumulated wealth; some authors add Mercury for speech.",
    3: "Mars signifies courage and siblings.",
    4: "Moon signifies the mother and emotional ground; Mercury is often added "
    "for schooling and Venus for vehicles.",
    5: "Jupiter signifies children and prior merit.",
    6: "Mars signifies enemies and injury; Saturn is commonly added for chronic illness and debt.",
    7: "Venus signifies the spouse and partnership.",
    8: "Saturn signifies longevity and what is hidden.",
    9: "Jupiter signifies dharma and the guru; the Sun is commonly added for the father.",
    10: "Mercury signifies profession in BPHS; the Sun, Jupiter and Saturn are "
    "each cited as karma karaka by different authors, so the 10th has the "
    "least settled karaka of the twelve.",
    11: "Jupiter signifies gains and elder siblings.",
    12: "Saturn signifies loss and confinement; Ketu is commonly added for moksha.",
}

# What a house governs, in the register a reader can act on. These are the
# classical significations condensed, not predictions.
HOUSE_GOVERNS: dict[int, str] = {
    1: "The body, vitality, temperament, and the direction a life takes. How you "
    "arrive anywhere before you have said anything.",
    2: "Accumulated wealth as distinct from income, speech, the family you were "
    "born into, food, and what you value enough to keep.",
    3: "Courage, initiative, younger siblings, the hands, short journeys, and "
    "self-made effort rather than inherited advantage.",
    4: "The mother, the home, land and vehicles, formal schooling, and the "
    "inner ground a person stands on when nothing external is holding them up.",
    5: "Children, creative and intellectual output, romance, speculation, and "
    "merit carried in from before this life.",
    6: "Daily work and service, debt, illness, litigation, competitors, and the "
    "discipline by which difficulty is metabolised rather than avoided.",
    7: "Marriage and business partnership, contracts, open dealings with others, "
    "and the qualities a person reliably draws toward themselves.",
    8: "Inheritance and other people's money, crisis and transformation, the "
    "occult, longevity, and what stays hidden until it is forced open.",
    9: "Fortune, the father, teachers and gurus, long journeys, higher learning, "
    "and the beliefs a person will not trade away.",
    10: "Career, public standing, authority, and action taken in the world where "
    "it can be seen and judged.",
    11: "Income as distinct from wealth, networks, elder siblings, patrons, and "
    "the fulfilment of stated desires.",
    12: "Loss and expenditure, foreign lands, seclusion and hospitals, sleep and "
    "dreams, and release from the whole apparatus.",
}
