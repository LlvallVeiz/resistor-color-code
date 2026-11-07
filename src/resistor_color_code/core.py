"""Core logic: decode band colours, encode values, E-series lookup.

Band layouts (IEC 60062):

- 4-band: digit digit multiplier tolerance
- 5-band: digit digit digit multiplier tolerance
- 6-band: digit digit digit multiplier tolerance temperature-coefficient

Resistance math:  R = (digits as an integer) x 10^(multiplier exponent).
"""

import math

from .tables import (
    ALIASES, ALL_COLORS, CHART_ORDER, DIGITS, E_SERIES, MULTIPLIERS,
    TEMPCOS, TOLERANCES,
)

_DIGIT_BY_VALUE = {v: k for k, v in DIGITS.items()}
_MULT_BY_EXP = {v: k for k, v in MULTIPLIERS.items()}


def normalize_color(color: str) -> str:
    """Lower-case a colour name and resolve aliases (grey -> gray)."""
    c = color.strip().lower()
    return ALIASES.get(c, c)


def _check_color(color: str, role: str) -> None:
    if color not in ALL_COLORS:
        raise ValueError(
            f"unknown colour {color!r} for the {role} band; "
            f"valid colours: {', '.join(ALL_COLORS)}"
        )


# ---------------------------------------------------------------------------
# Decode
# ---------------------------------------------------------------------------

def decode(colors: list[str]) -> dict:
    """Decode 4, 5 or 6 band colours.

    Returns dict(ohms, tolerance_pct, tempco_ppm|None, bands).
    Raises ValueError with a helpful message on invalid input.
    """
    colors = [normalize_color(c) for c in colors]
    n = len(colors)
    if n not in (4, 5, 6):
        raise ValueError(
            f"expected 4, 5 or 6 band colours, got {n}: {' '.join(colors)}"
        )
    n_digits = 2 if n == 4 else 3
    digit_colors = colors[:n_digits]
    mult_color = colors[n_digits]
    tol_color = colors[n_digits + 1]
    tempco_color = colors[n_digits + 2] if n == 6 else None

    for c in digit_colors:
        _check_color(c, "digit")
        if c not in DIGITS:
            raise ValueError(
                f"{c!r} cannot be a digit band (gold/silver/pink have no "
                f"digit value); digit bands must be one of: "
                f"{', '.join(DIGITS)}"
            )
    if DIGITS[digit_colors[0]] == 0:
        raise ValueError(
            "the first digit band cannot be black (a resistor value never "
            "starts with 0) — the bands may be in the wrong order"
        )
    _check_color(mult_color, "multiplier")
    _check_color(tol_color, "tolerance")
    if tol_color not in TOLERANCES:
        raise ValueError(
            f"{tol_color!r} is not a valid tolerance colour; use one of: "
            f"{', '.join(TOLERANCES)}"
        )
    if tempco_color is not None:
        _check_color(tempco_color, "temperature-coefficient")
        if tempco_color not in TEMPCOS:
            raise ValueError(
                f"{tempco_color!r} has no temperature-coefficient value; "
                f"use one of: {', '.join(TEMPCOS)}"
            )

    digits_value = 0
    for c in digit_colors:
        digits_value = digits_value * 10 + DIGITS[c]
    ohms = digits_value * (10.0 ** MULTIPLIERS[mult_color])
    return {
        "ohms": ohms,
        "tolerance_pct": TOLERANCES[tol_color],
        "tempco_ppm": TEMPCOS[tempco_color] if tempco_color else None,
        "bands": n,
    }


# ---------------------------------------------------------------------------
# E-series preferred values (IEC 60063)
# ---------------------------------------------------------------------------

def nearest_eseries(value: float, series: str = "E24") -> float:
    """Return the E-series preferred value nearest to ``value``.

    "Nearest" is measured on a log scale (ratio distance), which is the
    natural metric for preferred numbers: each series spaces its values
    geometrically so their tolerance windows tile the decade.
    """
    series = series.upper()
    if series not in E_SERIES:
        raise ValueError(
            f"unknown series {series!r}; use one of: "
            f"{', '.join(E_SERIES)} or 'exact'"
        )
    if value <= 0:
        raise ValueError("resistance must be positive")
    best: tuple[float, float] | None = None  # (log distance, candidate)
    for decade in range(-6, 13):
        scale = 10.0 ** decade
        for mantissa in E_SERIES[series]:
            cand = mantissa * scale
            dist = abs(math.log10(cand / value))
            if best is None or dist < best[0]:
                best = (dist, cand)
    assert best is not None
    return best[1]


# ---------------------------------------------------------------------------
# Encode
# ---------------------------------------------------------------------------

def _encode_significant(target: float, n_digits: int) -> tuple[list[str], float]:
    """Find (digit colours + multiplier colour, exact value) for a target
    using exactly ``n_digits`` significant digits, choosing the closest
    representable value."""
    lo, hi = 10 ** (n_digits - 1), 10 ** n_digits - 1
    best = None  # (error, exponent, digit_int, candidate)
    for exp in range(-3, 10):
        d = int(round(target / (10.0 ** exp)))
        if lo <= d <= hi:
            candidate = d * (10.0 ** exp)
            err = abs(candidate - target)
            if best is None or err < best[0]:
                best = (err, exp, d, candidate)
    if best is None:
        raise ValueError(
            f"{target:g} Ω is outside the range encodable with "
            f"{n_digits} significant digits"
        )
    _, exp, d, candidate = best
    digit_str = str(d).rjust(n_digits, "0")
    colors = [_DIGIT_BY_VALUE[int(ch)] for ch in digit_str]
    colors.append(_MULT_BY_EXP[exp])
    return colors, candidate


def encode(value: float, bands: int = 4, tolerance: str = "gold",
           tempco: str = "red", series: str = "E24") -> dict:
    """Encode a resistance in ohms as band colours.

    With ``series`` set to an E-series name (default ``"E24"``), the
    value is first snapped to the nearest IEC 60063 preferred value of
    that series (``target_ohms``); with ``series="exact"`` the value
    itself is the target.  The target is then expressed with the number
    of significant digits the band count provides, and ``exact_ohms``
    reports the value the returned colours actually decode to (which
    can differ from the target when the target needs more significant
    digits than the bands offer, e.g. an E96 value on a 4-band part).
    """
    if bands not in (4, 5, 6):
        raise ValueError(f"bands must be 4, 5 or 6, got {bands}")
    tolerance = normalize_color(tolerance)
    if tolerance not in TOLERANCES:
        raise ValueError(
            f"unknown tolerance colour {tolerance!r}; use one of: "
            f"{', '.join(TOLERANCES)}"
        )
    if bands == 6:
        tempco = normalize_color(tempco)
        if tempco not in TEMPCOS:
            raise ValueError(
                f"unknown tempco colour {tempco!r}; use one of: "
                f"{', '.join(TEMPCOS)}"
            )
    if value <= 0:
        raise ValueError("resistance must be positive "
                         "(0 Ω cannot be colour-coded)")

    series = series.upper() if isinstance(series, str) else series
    if series == "EXACT":
        target = float(value)
        series_name = "exact"
    else:
        target = nearest_eseries(value, series)
        series_name = series

    n_digits = 2 if bands == 4 else 3
    colors, exact = _encode_significant(target, n_digits)
    colors.append(tolerance)
    if bands == 6:
        colors.append(tempco)
    return {
        "colors": colors,
        "exact_ohms": exact,
        "target_ohms": target,
        "requested_ohms": float(value),
        "series": series_name,
        "bands": bands,
    }


# ---------------------------------------------------------------------------
# Colour chart (for the `table` subcommand)
# ---------------------------------------------------------------------------

def color_chart() -> list[dict[str, str]]:
    """Return the full IEC 60062 colour chart as a list of row dicts
    with string fields: color, digit, multiplier, tolerance, tempco."""
    rows = []
    for color in CHART_ORDER:
        digit = str(DIGITS[color]) if color in DIGITS else "—"
        if color in MULTIPLIERS:
            exp = MULTIPLIERS[color]
            mult = f"×10^{exp}" if exp >= 0 else f"×10^{exp}"
        else:
            mult = "—"
        tol = (f"±{TOLERANCES[color]:g}%"
               if color in TOLERANCES and color != "none" else "—")
        tempco = f"{TEMPCOS[color]}" if color in TEMPCOS else "—"
        rows.append({
            "color": color, "digit": digit, "multiplier": mult,
            "tolerance": tol, "tempco": tempco,
        })
    return rows
