#!/usr/bin/env python3
"""Assert-based tests for the resistor colour-code package.

Run:  python3 tests/test_resistor.py
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)

from resistor_color_code import (  # noqa: E402
    color_chart, decode, encode, format_ohms, nearest_eseries, parse_value,
)
from resistor_color_code.tables import E_SERIES  # noqa: E402


def expect_error(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError(f"expected ValueError from {fn.__name__}{args}")


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol * max(1.0, abs(b))


# --- decode: the classic textbook cases ------------------------------------

r = decode(["yellow", "violet", "red", "gold"])
assert r["ohms"] == 4700 and r["tolerance_pct"] == 5.0, r
assert r["tempco_ppm"] is None and r["bands"] == 4

r = decode(["brown", "black", "red", "gold"])
assert r["ohms"] == 1000 and r["tolerance_pct"] == 5.0, r

# 5-band: 2 2 1 x1 +-1% = 221 Ω
r = decode(["red", "red", "brown", "black", "brown"])
assert r["ohms"] == 221 and r["tolerance_pct"] == 1.0 and r["bands"] == 5, r

# 6-band: 3 3 0 x1 +-1%, red tempco = 330 Ω, 50 ppm/K
r = decode(["orange", "orange", "black", "black", "brown", "red"])
assert r["ohms"] == 330 and r["tolerance_pct"] == 1.0, r
assert r["tempco_ppm"] == 50, r

# pink multiplier (IEC 60062:2016): 22 x 0.001 = 0.022 Ω
r = decode(["red", "red", "pink", "gold"])
assert close(r["ohms"], 0.022, 1e-6), r

# aliases
r = decode(["grey", "red", "red", "silver"])
assert r["ohms"] == 8200 and r["tolerance_pct"] == 10.0, r

# --- decode: validation -----------------------------------------------------

expect_error(decode, ["red", "red", "red"])                      # too few
expect_error(decode, ["black", "black", "red", "gold"])         # leading 0
expect_error(decode, ["gold", "black", "red", "gold"])          # gold digit
expect_error(decode, ["red", "red", "red", "black"])            # bad tolerance
expect_error(decode, ["red", "red", "red", "red", "red", "gold"])  # bad tempco
expect_error(decode, ["red", "red", "beige", "gold"])           # unknown colour

# --- E-series tables: structural invariants --------------------------------

assert {k: len(v) for k, v in E_SERIES.items()} == {
    "E3": 3, "E6": 6, "E12": 12, "E24": 24, "E48": 48, "E96": 96,
}
# nesting: E48 is every other E96 value; E12 every other E24; E6 < E12 < E24
assert E_SERIES["E48"] == E_SERIES["E96"][::2]
assert E_SERIES["E12"] == E_SERIES["E24"][::2]
assert set(E_SERIES["E6"]) < set(E_SERIES["E12"]) < set(E_SERIES["E24"])
assert set(E_SERIES["E3"]) <= set(E_SERIES["E6"])

# --- nearest_eseries ---------------------------------------------------------

assert close(nearest_eseries(4701, "E24"), 4700)
assert close(nearest_eseries(5000, "E24"), 5100)     # log-scale nearest
assert close(nearest_eseries(999, "E12"), 1000)      # rolls into next decade
assert close(nearest_eseries(10000, "E96"), 10000)
assert close(nearest_eseries(0.47, "E24"), 0.47, 1e-6)
assert close(nearest_eseries(4750, "E96"), 4750)
expect_error(nearest_eseries, -5, "E24")
expect_error(nearest_eseries, 100, "E7")

# --- encode ------------------------------------------------------------------

# no snapping: 10000 Ω 4-band -> brown black orange + gold (original spec case)
r = encode(10000, bands=4, tolerance="gold", series="exact")
assert r["colors"] == ["brown", "black", "orange", "gold"], r
assert r["exact_ohms"] == 10000, r

# default E24 snapping: 4701 -> 4700 exactly codable
r = encode(4701)
assert r["target_ohms"] == 4700 and r["exact_ohms"] == 4700, r
assert r["colors"] == ["yellow", "violet", "red", "gold"], r

# E96 precision value on a 5-band part: 4750 = 475 x10
r = encode(4750, bands=5, tolerance="brown", series="E96")
assert r["target_ohms"] == 4750 and r["exact_ohms"] == 4750, r
assert r["colors"] == ["yellow", "violet", "green", "brown", "brown"], r

# same E96 target on a 4-band part: target stands, exact value is the
# closest 2-significant-digit value (within half a step)
r = encode(4750, bands=4, series="E96")
assert r["target_ohms"] == 4750 and r["exact_ohms"] != 4750, r
assert abs(r["exact_ohms"] - 4750) <= 50, r

# 6-band encode round-trips through decode, tempco included
r = encode(330, bands=6, tolerance="brown", tempco="red", series="exact")
assert r["colors"] == ["orange", "orange", "black", "black", "brown",
                       "red"], r
back = decode(r["colors"])
assert back["ohms"] == 330 and back["tempco_ppm"] == 50, back

# round-trip property on a spread of exact-mode values
for value, bands in ((47, 4), (9100, 4), (221, 5), (999, 5), (0.47, 4)):
    r = encode(value, bands=bands, series="exact")
    assert close(decode(r["colors"])["ohms"], value, 1e-9), (value, r)

expect_error(encode, 0)
expect_error(encode, 100, bands=3)
expect_error(encode, 100, tolerance="beige")

# --- colour chart ------------------------------------------------------------

rows = {row["color"]: row for row in color_chart()}
assert rows["red"]["digit"] == "2"
assert rows["gold"]["tolerance"] == "±5%"
assert rows["pink"]["multiplier"] == "×10^-3"
assert rows["gray"]["tempco"] == "1"

# --- value parsing / formatting ----------------------------------------------

assert parse_value("4700") == 4700
assert parse_value("4.7k") == 4700
assert parse_value("4k7") == 4700
assert parse_value("4R7") == 4.7
assert parse_value("1M") == 1_000_000
assert parse_value("0.47") == 0.47
expect_error(parse_value, "abc")
expect_error(parse_value, "4.7k5")

assert format_ohms(4700) == "4.7 kΩ"
assert format_ohms(10000) == "10 kΩ"
assert format_ohms(0.22) == "220 mΩ"
assert format_ohms(1_000_000) == "1 MΩ"

print("All tests passed.")
