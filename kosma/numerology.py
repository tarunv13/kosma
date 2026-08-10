"""Numerology, kept deliberately at arm's length from the Jyotish.

This is included because it was asked for and because it travels with Vedic
astrology in practice -- most Indian practitioners will give a mulank and a
bhagyank alongside a chart. It is *not* folded into the evidence gate, and it
casts no vote on any finding, for a plain reason: the gate's whole claim is
that two independent kinds of *chart* factor must agree, and a number derived
from the spelling of a name is not a chart factor. Letting it in would quietly
weaken the one guarantee this project makes.

So it sits in its own section, says which system produced each number, and
says where the systems disagree rather than picking one and hiding the choice.

Two systems are computed because two are in use and they do not agree:

* **Chaldean**, the older, which assigns values by sound and never uses 9 for
  a letter. This is what Indian numerology overwhelmingly uses.
* **Pythagorean**, the modern Western one, which simply walks A-I = 1-9.

The date-derived numbers (mulank and bhagyank) are not system-dependent and
are the ones classical Indian practice actually leans on.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

# ── Letter values ─────────────────────────────────────────────────────

_CHALDEAN: dict[str, int] = {}
for _letters, _value in (
    ("AIJQY", 1),
    ("BKR", 2),
    ("CGLS", 3),
    ("DMT", 4),
    ("EHNX", 5),
    ("UVW", 6),
    ("OZ", 7),
    ("FP", 8),
):
    for _ch in _letters:
        _CHALDEAN[_ch] = _value

_PYTHAGOREAN: dict[str, int] = {chr(ord("A") + i): (i % 9) + 1 for i in range(26)}

# Numbers held to carry their own meaning and not reduced further.
MASTER_NUMBERS = (11, 22, 33)

# The graha each number is tied to in Indian numerology. This is the join
# between the two systems, and the only place they are allowed to touch.
NUMBER_GRAHA: dict[int, str] = {
    1: "Sun",
    2: "Moon",
    3: "Jupiter",
    4: "Rahu",
    5: "Mercury",
    6: "Venus",
    7: "Ketu",
    8: "Saturn",
    9: "Mars",
}

NUMBER_MEANING: dict[int, str] = {
    1: "Leadership and self-direction. Works alone well and takes instruction badly.",
    2: "Sensitivity and partnership. Reads people accurately; decides slowly.",
    3: "Expansion, teaching and optimism. Generous, and prone to overcommitting.",
    4: "Unconventional method and disruption. Builds differently, at some social cost.",
    5: "Communication, commerce and adaptability. Quick, restless, hard to pin down.",
    6: "Beauty, comfort and relationship. Draws people; avoids necessary conflict.",
    7: "Detachment, research and interiority. Sees through things, including good ones.",
    8: "Endurance, structure and delayed reward. Late success that tends to hold.",
    9: "Force, courage and confrontation. Finishes things; starts some unnecessarily.",
}


def _reduce(n: int, *, keep_master: bool = True) -> int:
    """Sum digits until one remains, preserving the master numbers."""
    while n > 9:
        if keep_master and n in MASTER_NUMBERS:
            return n
        n = sum(int(d) for d in str(n))
    return n


def _letters_only(text: str) -> str:
    return "".join(ch for ch in text.upper() if ch.isalpha() and ch.isascii())


def _name_number(name: str, table: dict[str, int]) -> int | None:
    letters = _letters_only(name)
    if not letters:
        return None
    return _reduce(sum(table.get(ch, 0) for ch in letters))


@dataclass(frozen=True)
class NumberReading:
    number: int
    graha: str
    meaning: str
    method: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "graha": self.graha,
            "meaning": self.meaning,
            "method": self.method,
        }


def _reading(n: int, method: str) -> NumberReading:
    base = _reduce(n, keep_master=False)
    return NumberReading(
        number=n,
        graha=NUMBER_GRAHA[base],
        meaning=NUMBER_MEANING[base],
        method=method,
    )


def compute(name: str, birth: date) -> dict[str, Any]:
    """Every number this module will state, each labelled with its method."""
    mulank = _reduce(birth.day, keep_master=False)
    bhagyank = _reduce(sum(int(d) for d in f"{birth.year}{birth.month:02d}{birth.day:02d}"))

    chaldean = _name_number(name, _CHALDEAN)
    pythagorean = _name_number(name, _PYTHAGOREAN)

    out: dict[str, Any] = {
        "mulank": _reading(mulank, "Day of birth, reduced to a single digit.").as_dict(),
        "bhagyank": _reading(
            bhagyank,
            "Whole date of birth summed and reduced. Master numbers 11, 22 and "
            "33 are left unreduced.",
        ).as_dict(),
        "name_chaldean": None,
        "name_pythagorean": None,
        "systems_agree": None,
        "note": (
            "Numerology is reported beside the chart, never inside it. It casts "
            "no vote on any finding: the gate requires two independent kinds of "
            "chart factor to agree, and a number derived from a date or a "
            "spelling is not a chart factor. The mapping from number to graha "
            "is the standard Indian one, and is the only point where the two "
            "systems are joined."
        ),
        "name_note": (
            "Name numbers depend on spelling and on transliteration, so they "
            "change with a change of either. Treat them as the softest thing "
            "on this page."
        ),
    }

    if chaldean is not None:
        out["name_chaldean"] = _reading(
            chaldean,
            "Chaldean values, which assign by sound and never use 9 for a "
            "letter. This is the system Indian practice generally uses.",
        ).as_dict()
    if pythagorean is not None:
        out["name_pythagorean"] = _reading(
            pythagorean, "Pythagorean values, A-I = 1-9. The modern Western system."
        ).as_dict()
    if chaldean is not None and pythagorean is not None:
        out["systems_agree"] = chaldean == pythagorean
        if not out["systems_agree"]:
            out["disagreement"] = (
                f"The two systems disagree here — Chaldean gives {chaldean}, "
                f"Pythagorean gives {pythagorean}. Neither is reported as the "
                f"answer, because there is no basis in either tradition for "
                f"preferring one and the disagreement is the honest result."
            )
    return out
