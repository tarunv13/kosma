"""
The twenty-seven nakshatras as a knowledge table, not a name list.

A Moon in Ashwini is not a Moon in Aries. The sign gives one layer; the
nakshatra carries a ruling deity, a symbol, a temperament class, a motivating
aim, an animal (yoni), and a planetary lord that is frequently *not* the sign
lord. Reading only the rashi throws all of that away, and it is the single
most common thing a language model gets wrong when it is asked to "know"
astrology rather than being handed the data.

Contested entries
-----------------
Two fields in this table are genuinely unsettled between authorities:

* ``purushartha`` — most published tables run a mechanical dharma/artha/kama/
  moksha cycle from Ashwini. Others assign the aim from the presiding deity,
  which moves Moola and Revati in particular. Both conventions are recorded.
* ``body_part`` — Kalapurusha assignments vary widely by source and are given
  here for reference only. They are never used as evidence and never inform
  anything health-related.

Sources
-------
* Brihat Parashara Hora Shastra ch. 3 — nakshatra lords and spans.
* Taittiriya Brahmana I.5 — presiding deities.
* Muhurta Chintamani ch. 2 — activity classes (gana, and the seven-fold
  temperament used for electional work).
"""

from __future__ import annotations

from dataclasses import dataclass

from .vedic_engine import NAKSHATRAS


@dataclass(frozen=True)
class Nakshatra:
    """Everything classical about one lunar mansion."""

    index: int  # 0-based
    name: str
    lord: str
    deity: str
    symbol: str
    gana: str  # deva / manushya / rakshasa
    purushartha: str  # by the mechanical cycle
    purushartha_alt: str | None  # by deity, where authors differ
    yoni: str
    temperament: str  # kshipra / mridu / tikshna / ugra / chara / dhruva / mishra
    body_part: str
    signification: str

    @property
    def span(self) -> tuple[float, float]:
        """Start and end sidereal longitude of the nakshatra."""
        width = 360.0 / 27.0
        return self.index * width, (self.index + 1) * width

    @property
    def summary(self) -> str:
        return (
            f"{self.name}, ruled by {self.lord}, deity {self.deity}, "
            f"symbol {self.symbol}, {self.gana} gana, {self.temperament} in "
            f"temperament, oriented to {self.purushartha}"
        )


# index, name, lord, deity, symbol, gana, purushartha, alt, yoni, temperament,
# body part, signification
_TABLE: tuple[tuple[int, str, str, str, str, str, str, str | None, str, str, str, str], ...] = (
    (
        0,
        "Ashwini",
        "Ketu",
        "the Ashwini Kumaras",
        "a horse's head",
        "deva",
        "dharma",
        None,
        "horse",
        "kshipra",
        "knees",
        "The physician twins. Speed, first arrival, the healing impulse, the "
        "urge to initiate and to rescue.",
    ),
    (
        1,
        "Bharani",
        "Venus",
        "Yama",
        "the yoni",
        "manushya",
        "artha",
        None,
        "elephant",
        "ugra",
        "head",
        "The bearer and the restrainer. Gestation, moral weight, the capacity "
        "to hold extremity without flinching.",
    ),
    (
        2,
        "Krittika",
        "Sun",
        "Agni",
        "a razor and flame",
        "rakshasa",
        "kama",
        None,
        "sheep",
        "mishra",
        "waist and hips",
        "The cutter and the purifier. Sharpness, burning away of dross, criticism that clarifies.",
    ),
    (
        3,
        "Rohini",
        "Moon",
        "Brahma (Prajapati)",
        "a cart",
        "manushya",
        "moksha",
        None,
        "serpent",
        "dhruva",
        "shins and forehead",
        "The red one, most beloved of the Moon. Fertility, growth, beauty, material fruition.",
    ),
    (
        4,
        "Mrigashira",
        "Mars",
        "Soma",
        "a deer's head",
        "deva",
        "dharma",
        None,
        "serpent",
        "mridu",
        "eyebrows",
        "The searching deer. Restless seeking, curiosity, the scent of "
        "something better just over the ridge.",
    ),
    (
        5,
        "Ardra",
        "Rahu",
        "Rudra",
        "a teardrop",
        "manushya",
        "artha",
        None,
        "dog",
        "tikshna",
        "eyes and hair",
        "The storm-god's mansion. Rupture, grief that clears the air, the "
        "hunger to understand by taking apart.",
    ),
    (
        6,
        "Punarvasu",
        "Jupiter",
        "Aditi",
        "a quiver of arrows",
        "deva",
        "kama",
        None,
        "cat",
        "chara",
        "fingers and nose",
        "Return of the light. Renewal after loss, homecoming, inexhaustible second chances.",
    ),
    (
        7,
        "Pushya",
        "Saturn",
        "Brihaspati",
        "a cow's udder",
        "deva",
        "moksha",
        None,
        "sheep",
        "kshipra",
        "mouth and face",
        "The most auspicious nourisher. Sustenance, priestly care, steady provision for others.",
    ),
    (
        8,
        "Ashlesha",
        "Mercury",
        "the Nagas",
        "a coiled serpent",
        "rakshasa",
        "dharma",
        None,
        "cat",
        "tikshna",
        "ears and joints",
        "The embrace of the serpent. Hypnotic insight, entwinement, kundalini and cunning alike.",
    ),
    (
        9,
        "Magha",
        "Ketu",
        "the Pitris",
        "a royal throne",
        "rakshasa",
        "artha",
        None,
        "rat",
        "ugra",
        "nose and lips",
        "The seat of the ancestors. Lineage, inherited authority, obligation "
        "to those who came before.",
    ),
    (
        10,
        "Purva Phalguni",
        "Venus",
        "Bhaga",
        "the front legs of a bed",
        "manushya",
        "kama",
        None,
        "rat",
        "ugra",
        "right hand",
        "The couch of pleasure. Rest, union, creative leisure, enjoyment as a legitimate aim.",
    ),
    (
        11,
        "Uttara Phalguni",
        "Sun",
        "Aryaman",
        "the back legs of a bed",
        "manushya",
        "moksha",
        None,
        "cow",
        "dhruva",
        "left hand",
        "Patronage and contract. Friendship formalised, generosity that carries obligation.",
    ),
    (
        12,
        "Hasta",
        "Moon",
        "Savitr",
        "an open hand",
        "deva",
        "dharma",
        None,
        "buffalo",
        "kshipra",
        "hands",
        "The hand that makes. Craft, dexterity, sleight of hand, the power to "
        "materialise what is imagined.",
    ),
    (
        13,
        "Chitra",
        "Mars",
        "Tvashtar",
        "a bright jewel",
        "rakshasa",
        "artha",
        None,
        "tiger",
        "mridu",
        "neck and forehead",
        "The celestial architect's jewel. Design, brilliance, form made deliberately beautiful.",
    ),
    (
        14,
        "Swati",
        "Rahu",
        "Vayu",
        "a young shoot in the wind",
        "deva",
        "kama",
        None,
        "buffalo",
        "chara",
        "chest",
        "The independent reed. Self-direction, trade, movement, flexibility "
        "that refuses to be tied.",
    ),
    (
        15,
        "Vishakha",
        "Jupiter",
        "Indra and Agni",
        "a triumphal arch",
        "rakshasa",
        "moksha",
        None,
        "tiger",
        "mishra",
        "arms and breasts",
        "The forked branch. Determined pursuit of a goal, ambition with two aims held at once.",
    ),
    (
        16,
        "Anuradha",
        "Saturn",
        "Mitra",
        "a lotus",
        "deva",
        "dharma",
        None,
        "deer",
        "mridu",
        "stomach",
        "The friend who keeps faith. Devotion, alliance across distance, "
        "success found away from home.",
    ),
    (
        17,
        "Jyeshtha",
        "Mercury",
        "Indra",
        "a circular amulet",
        "rakshasa",
        "artha",
        None,
        "deer",
        "tikshna",
        "right side and neck",
        "The eldest. Seniority, protective power, the loneliness and burden of rank.",
    ),
    (
        18,
        "Moola",
        "Ketu",
        "Nirriti",
        "a bunch of roots",
        "rakshasa",
        "kama",
        "moksha",
        "dog",
        "tikshna",
        "feet",
        "The root. Investigation to the bottom of things, dissolution, "
        "uprooting that precedes real change.",
    ),
    (
        19,
        "Purva Ashadha",
        "Venus",
        "Apas",
        "a winnowing basket",
        "manushya",
        "moksha",
        None,
        "monkey",
        "ugra",
        "thighs and back",
        "The invincible waters. Undefeated conviction, purification, declarative confidence.",
    ),
    (
        20,
        "Uttara Ashadha",
        "Sun",
        "the Vishvedevas",
        "an elephant tusk",
        "manushya",
        "dharma",
        None,
        "mongoose",
        "dhruva",
        "thighs and waist",
        "The later victory. Lasting achievement won slowly, integrity that outlasts opposition.",
    ),
    (
        21,
        "Shravana",
        "Moon",
        "Vishnu",
        "an ear",
        "deva",
        "artha",
        None,
        "monkey",
        "chara",
        "ears",
        "The listener. Learning by hearing, scripture, counsel, reputation "
        "built on what one has absorbed.",
    ),
    (
        22,
        "Dhanishtha",
        "Mars",
        "the eight Vasus",
        "a drum",
        "rakshasa",
        "kama",
        None,
        "lion",
        "chara",
        "back",
        "The drum of wealth. Rhythm, music, abundance, the pulse that organises a group.",
    ),
    (
        23,
        "Shatabhisha",
        "Rahu",
        "Varuna",
        "an empty circle",
        "rakshasa",
        "moksha",
        None,
        "horse",
        "chara",
        "jaw and right thigh",
        "The hundred healers. Secrecy, medicine, the veil, solitary research into hidden causes.",
    ),
    (
        24,
        "Purva Bhadrapada",
        "Jupiter",
        "Aja Ekapada",
        "a two-faced man",
        "manushya",
        "dharma",
        None,
        "lion",
        "ugra",
        "ribs and left side",
        "The one-footed goat. Ascetic fire, extremity, the visionary who is "
        "uncomfortable in ordinary company.",
    ),
    (
        25,
        "Uttara Bhadrapada",
        "Saturn",
        "Ahir Budhnya",
        "a serpent in the deep",
        "manushya",
        "artha",
        None,
        "cow",
        "dhruva",
        "shins and soles",
        "The serpent of the depths. Stillness, deep counsel, wisdom that surfaces only when asked.",
    ),
    (
        26,
        "Revati",
        "Mercury",
        "Pushan",
        "a fish",
        "deva",
        "kama",
        "moksha",
        "elephant",
        "mridu",
        "ankles and abdomen",
        "The shepherd of safe passage. Completion, protection on journeys, "
        "the last mansion before the cycle begins again.",
    ),
)

NAKSHATRA_TABLE: dict[str, Nakshatra] = {
    row[1]: Nakshatra(
        index=row[0],
        name=row[1],
        lord=row[2],
        deity=row[3],
        symbol=row[4],
        gana=row[5],
        purushartha=row[6],
        purushartha_alt=row[7],
        yoni=row[8],
        temperament=row[9],
        body_part=row[10],
        signification=row[11],
    )
    for row in _TABLE
}

# Fields that authorities disagree on. The evidence gate never counts these.
CONTESTED_FIELDS = ("purushartha", "body_part")

GANA_NOTE = (
    "Gana (deva, manushya, rakshasa) is a temperament class used mainly in "
    "compatibility work; it is not a moral ranking."
)

TEMPERAMENT_NOTE = (
    "The seven-fold temperament (kshipra, mridu, tikshna, ugra, chara, dhruva, "
    "mishra) is an electional classification from Muhurta Chintamani, "
    "describing what kind of action the mansion favours."
)


def by_index(index: int) -> Nakshatra:
    """Nakshatra by 0-based index."""
    return NAKSHATRA_TABLE[NAKSHATRAS[index % 27]]


def by_longitude(longitude: float) -> Nakshatra:
    """Nakshatra holding a sidereal longitude."""
    return by_index(int((longitude % 360.0) / (360.0 / 27.0)))


def by_name(name: str) -> Nakshatra | None:
    return NAKSHATRA_TABLE.get(name)


def pada_lord(longitude: float) -> str:
    """Navamsa lord of the pada holding ``longitude``.

    Each nakshatra pada is one navamsa of 3°20'. The pada's lord is the ruler
    of the navamsa sign, which is what gives two planets in the same nakshatra
    but different padas materially different readings.
    """
    from .dignity import SIGN_LORDS
    from .vedic_engine import SIGNS, navamsa_sign_idx

    return SIGN_LORDS[SIGNS[navamsa_sign_idx(longitude)]]


def describe(longitude: float) -> dict[str, object]:
    """Full nakshatra description for a longitude, contested fields flagged."""
    nak = by_longitude(longitude)
    width = 360.0 / 27.0
    deg_in = (longitude % 360.0) - nak.index * width
    pada = int(deg_in / (width / 4)) + 1
    return {
        "name": nak.name,
        "pada": pada,
        "lord": nak.lord,
        "pada_lord": pada_lord(longitude),
        "deity": nak.deity,
        "symbol": nak.symbol,
        "gana": nak.gana,
        "yoni": nak.yoni,
        "temperament": nak.temperament,
        "signification": nak.signification,
        "purushartha": nak.purushartha,
        "purushartha_contested": (
            f"some authors assign {nak.purushartha_alt} from the deity instead"
            if nak.purushartha_alt
            else None
        ),
        "body_part": nak.body_part,
        "body_part_note": "Kalapurusha assignments vary by source; reference only.",
    }
