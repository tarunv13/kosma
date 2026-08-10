"""Colour has to mean something, and has to stay readable.

Two properties are pinned here. Colour must come from the house rather than
from its verdict, because a red house tells a reader how to feel before they
have read a word. And every value must clear WCAG AAA against the ground it
sits on, because a palette that only works in theory is a palette that
excludes people in practice.
"""

from __future__ import annotations

import pytest

from kosma import themes

GROUND = "#FDFCF9"
AAA = 7.0


def _luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = channel(r), channel(g), channel(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


HOUSES = range(1, 13)


def test_every_house_has_a_theme() -> None:
    assert set(themes.HOUSE_THEMES) == set(HOUSES)


@pytest.mark.parametrize("house", HOUSES)
def test_ink_clears_aaa_on_the_page_ground(house: int) -> None:
    t = themes.theme_for(house)
    ratio = _contrast(t.ink, GROUND)
    assert ratio >= AAA, f"house {house} ink is {ratio:.2f}:1 against the page"


@pytest.mark.parametrize("house", HOUSES)
def test_ink_clears_aaa_on_its_own_wash(house: int) -> None:
    """A theme's text sits on that theme's panel, not on the bare page."""
    t = themes.theme_for(house)
    ratio = _contrast(t.ink, t.wash)
    assert ratio >= AAA, f"house {house} ink is {ratio:.2f}:1 on its own wash"


@pytest.mark.parametrize("house", HOUSES)
def test_wash_stays_pale_enough_to_carry_body_text(house: int) -> None:
    t = themes.theme_for(house)
    assert _luminance(t.wash) > 0.75, f"house {house} wash is too dark for a panel"


def test_hues_are_distinguishable_from_each_other() -> None:
    """Twelve themes are useless if two of them look identical."""
    seen = [t.hue for t in themes.HOUSE_THEMES.values()]
    assert len(set(seen)) == 12


def test_themes_are_not_a_verdict_palette() -> None:
    """No house may be assigned the colours of success or failure.

    The 8th house is difficult and is not an error, and the 11th is
    favourable and is not a confirmation dialog. Colour here describes the
    subject, never the result, so the traditional red/green signalling pair
    must not appear.
    """
    for house, t in themes.HOUSE_THEMES.items():
        r, g, b = (int(t.hue[i : i + 2], 16) for i in (1, 3, 5))
        assert not (r > 190 and g < 90 and b < 90), f"house {house} reads as an error red"
        assert not (g > 150 and r < 90 and b < 90), f"house {house} reads as a success green"


def test_every_theme_explains_itself() -> None:
    """The palette is derived from element and karaka, so it can be defended."""
    for house, t in themes.HOUSE_THEMES.items():
        assert t.element in themes.ELEMENTS, f"house {house} has no element"
        assert len(t.why) > 40, f"house {house} does not say why it is this colour"
        assert t.name, f"house {house} has no name"


EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def test_no_dash_reaches_the_reader() -> None:
    for t in themes.HOUSE_THEMES.values():
        assert EM_DASH not in t.why
        assert EN_DASH not in t.why
    assert EM_DASH not in themes.PALETTE_NOTE


def test_palette_note_states_the_rule() -> None:
    assert "whatever the chart says" in themes.PALETTE_NOTE
