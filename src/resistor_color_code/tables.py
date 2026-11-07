"""Colour-code and preferred-value tables (IEC 60062 / IEC 60063).

All values in this module follow the printed IEC 60062:2016 colour chart
and the IEC 60063 E-series of preferred numbers.  See ``docs/RESEARCH.md``
for sources and for the few places where older charts differ.
"""

# ---------------------------------------------------------------------------
# IEC 60062 colour tables
# ---------------------------------------------------------------------------

#: Significant-figure value of each digit colour.
DIGITS: dict[str, int] = {
    "black": 0, "brown": 1, "red": 2, "orange": 3, "yellow": 4,
    "green": 5, "blue": 6, "violet": 7, "gray": 8, "white": 9,
}

#: Colour -> power of ten for the multiplier band.  Pink (x0.001) was
#: added by IEC 60062:2016.
MULTIPLIERS: dict[str, int] = {
    "pink": -3, "silver": -2, "gold": -1, "black": 0, "brown": 1,
    "red": 2, "orange": 3, "yellow": 4, "green": 5, "blue": 6,
    "violet": 7, "gray": 8, "white": 9,
}

#: Colour -> tolerance in percent.  "none" = no tolerance band (+-20 %).
#: Note: IEC 60062:2016 also assigns tolerances to orange (+-0.05 %),
#: yellow (+-0.02 %) and gray (+-0.01 %); the values used here for gray
#: (+-0.05 %) follow the older, still widely printed chart.  See
#: docs/RESEARCH.md.
TOLERANCES: dict[str, float] = {
    "brown": 1.0, "red": 2.0, "orange": 3.0, "yellow": 4.0,
    "green": 0.5, "blue": 0.25, "violet": 0.1, "gray": 0.05,
    "gold": 5.0, "silver": 10.0, "none": 20.0,
}

#: Colour -> temperature coefficient in ppm/K (6th band), IEC 60062:2016.
TEMPCOS: dict[str, int] = {
    "black": 250, "brown": 100, "red": 50, "orange": 15,
    "yellow": 25, "green": 20, "blue": 10, "violet": 5, "gray": 1,
}

#: Common alternative spellings accepted on input.
ALIASES: dict[str, str] = {"grey": "gray", "purple": "violet"}

#: Every colour name the tool understands (plus "none").
ALL_COLORS: list[str] = sorted(
    set(DIGITS) | set(MULTIPLIERS) | set(TEMPCOS) | {"none"}
)

#: Display order for the colour chart.
CHART_ORDER: list[str] = [
    "black", "brown", "red", "orange", "yellow", "green", "blue",
    "violet", "gray", "white", "gold", "silver", "pink",
]

# ---------------------------------------------------------------------------
# IEC 60063 E-series of preferred numbers (mantissas in the decade 1-10)
# ---------------------------------------------------------------------------
#
# Only the two "base" series are listed literally.  The published tables
# nest exactly: E48 is every other E96 value, E12 is every other E24
# value, and E6 is every other E12 value (verified against the sources in
# docs/RESEARCH.md), so the rest are derived -- that removes a whole class
# of transcription typos, and tests assert the resulting lengths.

_E24: list[int] = [  # two-significant-figure mantissas x10
    10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30,
    33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91,
]

_E96: list[int] = [  # three-significant-figure mantissas x100
    100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130,
    133, 137, 140, 143, 147, 150, 154, 158, 162, 165, 169, 174,
    178, 182, 187, 191, 196, 200, 205, 210, 215, 221, 226, 232,
    237, 243, 249, 255, 261, 267, 274, 280, 287, 294, 301, 309,
    316, 324, 332, 340, 348, 357, 365, 374, 383, 392, 402, 412,
    422, 432, 442, 453, 464, 475, 487, 499, 511, 523, 536, 549,
    562, 576, 590, 604, 619, 634, 649, 665, 681, 698, 715, 732,
    750, 768, 787, 806, 825, 845, 866, 887, 909, 931, 953, 976,
]

#: Series name -> mantissas in [1, 10).
E_SERIES: dict[str, list[float]] = {
    "E3": [1.0, 2.2, 4.7],
    "E6": [m / 10 for m in _E24[::4]],
    "E12": [m / 10 for m in _E24[::2]],
    "E24": [m / 10 for m in _E24],
    "E48": [m / 100 for m in _E96[::2]],
    "E96": [m / 100 for m in _E96],
}

#: The tolerance each series is conventionally paired with (percent).
E_SERIES_TOLERANCE: dict[str, float] = {
    "E3": 20.0, "E6": 20.0, "E12": 10.0,
    "E24": 5.0, "E48": 2.0, "E96": 1.0,
}
