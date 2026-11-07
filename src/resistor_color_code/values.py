"""Parsing and formatting of resistance values.

The parser understands plain numbers (``4700``), decimal + suffix
(``4.7k``, ``1M``) and the RKM-style infix notation defined alongside
the colour code in IEC 60062 (``4k7``, ``4R7``), where the suffix letter
takes the place of the decimal point.
"""

import re

_SUFFIX_MULT: dict[str, float] = {
    "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9, "m": 1e-3, "R": 1.0, "r": 1.0,
}
_VALUE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*([kKMGmRr])?\s*(\d+)?$")


def parse_value(text: str) -> float:
    """Parse a resistance string into ohms.

    Accepts ``4700``, ``4.7k``, ``4k7``, ``1M``, ``4R7``, ``0.47`` ...
    Raises ValueError with examples on malformed input.
    """
    s = text.strip().replace("Ω", "").replace("ohm", "").strip()
    m = _VALUE_RE.match(s)
    if not m:
        raise ValueError(
            f"cannot parse resistance value {text!r}; examples: 4700, "
            f"4.7k, 4k7, 1M, 4R7"
        )
    whole, suffix, frac = m.group(1), m.group(2), m.group(3)
    mult = _SUFFIX_MULT[suffix] if suffix else 1.0
    if frac is not None:
        if "." in whole:
            raise ValueError(
                f"cannot parse resistance value {text!r}: use either "
                f"'4.7k' or '4k7', not both notations at once"
            )
        return (int(whole) + int(frac) / (10 ** len(frac))) * mult
    return float(whole) * mult


def _trim(num: float, decimals: int) -> str:
    s = f"{num:.{decimals}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def format_ohms(ohms: float) -> str:
    """Format a resistance nicely: 4700 -> '4.7 kΩ', 0.22 -> '220 mΩ'."""
    for unit, scale in (("GΩ", 1e9), ("MΩ", 1e6), ("kΩ", 1e3), ("Ω", 1.0)):
        if ohms >= scale:
            scaled = ohms / scale
            decimals = 0 if scaled >= 100 else (1 if scaled >= 10 else 2)
            return f"{_trim(scaled, decimals)} {unit}"
    return f"{_trim(ohms * 1e3, 1)} mΩ"


def raw_ohms(ohms: float) -> str:
    """Format as a plain ohm figure: 4700 -> '4700 Ω'."""
    if ohms == int(ohms) and ohms < 1e15:
        return f"{int(ohms)} Ω"
    return f"{ohms:g} Ω"
