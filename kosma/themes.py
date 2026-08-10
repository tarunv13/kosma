"""A colour per house, taken from what the house already is.

Colour in this interface carries meaning, so it cannot be decoration and it
cannot be a verdict. Two rules produce every value below.

**Colour comes from the house, never from the result.** Painting a
well-supported house green and a strained one red tells a reader how to feel
before they have read a word, and it makes the 8th house look like an error
message when it is simply the house of crisis and inheritance. A house keeps
its colour whatever the chart says about it, so the reader learns the palette
once and can then navigate by it.

**The palette is derived, not invented.** Each house already carries an
element through its sign and a natural significator through its karaka, and
those associations are old and consistent. Fire houses run warm, water houses
run cool, earth houses run green, air houses run pale and open. Where the
karaka pulls against the element the karaka wins, because a reader recognises
Venus in the 7th more readily than they recognise cardinal air.

Every colour is checked against the parchment ground the interface uses for
contrast, so no theme is only distinguishable by hue: each has an ink value
dark enough to read as body text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The four classical elements, by sign index from Aries.
ELEMENTS = ("fire", "earth", "air", "water")


@dataclass(frozen=True)
class HouseTheme:
    house: int
    name: str
    """A short name for the mood, shown as the section's label."""
    element: str
    hue: str
    """A CSS colour for accents: rules, chips, the dot on a section."""
    ink: str
    """A darker value of the same hue, safe for text on the light ground."""
    wash: str
    """A very pale value, for a panel's background."""
    why: str
    """Why this house has this colour. Shown on request, never invented."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "house": self.house,
            "name": self.name,
            "element": self.element,
            "hue": self.hue,
            "ink": self.ink,
            "wash": self.wash,
            "why": self.why,
        }


# Contrast ratios in the comments are against #FDFCF9, the parchment ground.
HOUSE_THEMES: dict[int, HouseTheme] = {
    1: HouseTheme(
        house=1,
        name="The self arriving",
        element="fire",
        hue="#C2703D",
        ink="#7A3E17",  # 8.09:1 on the ground, 7.46:1 on its own wash
        wash="#FBF1E9",
        why=(
            "Fire, and the Sun's house of the body and the visible self. Warm "
            "and forward, the colour of something walking into a room."
        ),
    ),
    2: HouseTheme(
        house=2,
        name="What you hold",
        element="earth",
        hue="#5C7A4A",
        ink="#33502A",  # 8.82:1 on the ground, 8.12:1 on its own wash
        wash="#F0F4EC",
        why=(
            "Earth, and the house of accumulated wealth, food and family. "
            "Green because it is the house of what grows and is kept."
        ),
    ),
    3: HouseTheme(
        house=3,
        name="Nerve and effort",
        element="air",
        hue="#B65C3A",
        ink="#7C3418",  # 8.67:1 on the ground, 7.82:1 on its own wash
        wash="#FAEEE9",
        why=(
            "Mars runs this house of courage and initiative, so it takes his "
            "heat rather than the cooler tone air would otherwise give it."
        ),
    ),
    4: HouseTheme(
        house=4,
        name="The ground under you",
        element="water",
        hue="#3F7A80",
        ink="#1F5054",  # 8.77:1 on the ground, 7.98:1 on its own wash
        wash="#EAF3F4",
        why=(
            "Water, the Moon, the mother and the home. Cool and held, the "
            "colour of somewhere you can stop performing."
        ),
    ),
    5: HouseTheme(
        house=5,
        name="What you make",
        element="fire",
        hue="#8C5AA8",
        ink="#59306E",  # 9.88:1 on the ground, 8.84:1 on its own wash
        wash="#F4EDF8",
        why=(
            "Fire by element, but the house of children, creation and merit "
            "carried in from before, which the violet register suits better "
            "than a plain flame."
        ),
    ),
    6: HouseTheme(
        house=6,
        name="The daily grind",
        element="earth",
        hue="#5F6B78",
        ink="#38424D",  # 9.96:1 on the ground, 9.03:1 on its own wash
        wash="#EFF1F4",
        why=(
            "Work, debt, illness and opposition, run by Mars and Saturn "
            "between them. Steel, because this is the house of what has to be "
            "ground down rather than enjoyed."
        ),
    ),
    7: HouseTheme(
        house=7,
        name="Who you meet halfway",
        element="air",
        hue="#B4567A",
        ink="#7A2C4C",  # 8.93:1 on the ground, 8.00:1 on its own wash
        wash="#FAECF1",
        why=(
            "Venus, marriage and open dealings with others. Rose is her "
            "colour and the reader will already expect it here."
        ),
    ),
    8: HouseTheme(
        house=8,
        name="What turns over",
        element="water",
        hue="#4E5A94",
        ink="#2C3566",  # 11.32:1 on the ground, 10.12:1 on its own wash
        wash="#EDEFF7",
        why=(
            "Crisis, inheritance, the occult and longevity. Deep indigo: dim "
            "rather than alarming, because this house is difficult and is not "
            "a warning."
        ),
    ),
    9: HouseTheme(
        house=9,
        name="What you believe",
        element="fire",
        hue="#B08829",
        ink="#5E460C",  # 8.68:1 on the ground, 8.05:1 on its own wash
        wash="#FAF3E2",
        why=(
            "Jupiter, fortune, the father and the teacher. Saffron, the "
            "colour the tradition gives Guru and gives to what is taught."
        ),
    ),
    10: HouseTheme(
        house=10,
        name="What you are seen doing",
        element="earth",
        hue="#8A6A3E",
        ink="#57411F",  # 9.38:1 on the ground, 8.56:1 on its own wash
        wash="#F6F1E8",
        why=(
            "Career, standing and action taken where it can be judged. "
            "Bronze, a worked metal rather than a bright one."
        ),
    ),
    11: HouseTheme(
        house=11,
        name="What comes in",
        element="air",
        hue="#3B7A8C",
        ink="#1E4E5C",  # 8.90:1 on the ground, 8.10:1 on its own wash
        wash="#E9F3F6",
        why=(
            "Income, networks and gains, which arrive through other people. "
            "Cyan is the house's air element without the coolness of the 4th."
        ),
    ),
    12: HouseTheme(
        house=12,
        name="What you let go",
        element="water",
        hue="#6A6E8A",
        ink="#3E4260",  # 9.51:1 on the ground, 8.59:1 on its own wash
        wash="#F0F0F5",
        why=(
            "Loss, seclusion, foreign places and release. The quietest colour "
            "here, close to grey, because this is the house of dissolving."
        ),
    ),
}


def theme_for(house: int) -> HouseTheme:
    return HOUSE_THEMES[house]


def all_themes() -> list[dict[str, Any]]:
    return [HOUSE_THEMES[h].as_dict() for h in range(1, 13)]


PALETTE_NOTE = (
    "Each house keeps its own colour whatever the chart says about it. The "
    "colours come from the element and the graha the tradition already gives "
    "the house, so fire houses run warm and water houses run cool. Nothing "
    "here is coloured by whether the reading came out well: a red house would "
    "tell you how to feel before you had read it, and would make the 8th look "
    "like a fault when it is simply the house of crisis."
)
