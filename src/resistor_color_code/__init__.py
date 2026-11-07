"""Resistor colour-code tool (IEC 60062) with E-series lookup (IEC 60063)."""

from .core import color_chart, decode, encode, nearest_eseries
from .values import format_ohms, parse_value

__all__ = [
    "color_chart", "decode", "encode", "nearest_eseries",
    "format_ohms", "parse_value",
]
__version__ = "1.0.0"
