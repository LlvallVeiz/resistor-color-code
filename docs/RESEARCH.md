# Background & Research — Resistor Colour Code

This document records the standards and references the implementation is
built on, and the places where the code makes a documented choice between
differing published charts. Every source below was consulted while
writing the code.

## 1. The colour code: IEC 60062

Resistor colour coding is defined by **IEC 60062, "Marking codes for
resistors and capacitors"** — first standardised as IEC 62:1952, with the
current edition **IEC 60062:2016** (consolidated with Amendment 1 as
IEC 60062:2016+AMD1:2019 CSV). The standard "specifies designation and
marking codes for capacitors and resistors [and] provides coding methods
for the resistance or capacitance value and its tolerance, including
colour coding for resistors" [1][2].

The band layouts implemented here are:

| Bands | Layout |
|---|---|
| 3 | digit, digit, multiplier (no tolerance band → ±20 %) |
| 4 | digit, digit, multiplier, tolerance |
| 5 | digit, digit, digit, multiplier, tolerance |
| 6 | digit, digit, digit, multiplier, tolerance, temperature coefficient |

(3-band parts exist but are a legacy ±20 % form; this tool accepts 4–6.)

The colour assignments in `tables.py` follow the IEC 60062:2016 chart
as reproduced in [3]:

- Digits: black 0 … white 9.
- Multipliers: ×10⁰–×10⁹ (black…white), gold ×10⁻¹, silver ×10⁻², and
  **pink ×10⁻³ — a colour introduced by the 2016 edition** [2][4]; the
  tool supports it as a multiplier.
- Tolerances: brown ±1 %, red ±2 %, green ±0.5 %, blue ±0.25 %,
  violet ±0.1 %, gold ±5 %, silver ±10 %, no band ±20 %.
- Temperature coefficients (6th band, ppm/K): black 250, brown 100,
  red 50, orange 15, yellow 25, green 20, blue 10, violet 5, **grey 1** [3].

### Documented deviations / chart differences

- **Grey tolerance.** IEC 60062:2016 lists grey tolerance as ±0.01 %
  (and also assigns orange ±0.05 % and yellow ±0.02 %); many older and
  still-printed charts list grey as ±0.05 % and omit the orange/yellow
  tolerance values [3][4][5]. This tool follows the widely printed chart
  (grey ±0.05 %, orange ±3 %, yellow ±4 %) because those are the values
  found on common hobbyist/industrial parts, and treats the 2016-only
  values as out of scope. The temperature-coefficient table, where the
  sources agree, follows 2016 (including grey = 1 ppm/K).
- Colour names: the standard spells "grey"; the tool accepts both
  "grey" and "gray", plus "purple" as an alias for violet, as a
  user-input convenience only.

### Reading direction

Real parts are read from the end where the bands are grouped closest
together, with the tolerance band last [5]. The tool cannot see a
physical part, so it validates instead: a leading black digit band is
rejected with a hint that the order may be reversed, because no
resistance value has a leading zero.

## 2. Preferred values: the E-series (IEC 60063)

Manufactured resistors come in **preferred values** defined by
**IEC 60063** (first published as IEC 63:1952/1963; current edition
IEC 60063:2015) [6][7]. Each E-series divides a decade into N
geometrically spaced steps, with nominal ratio 10^(1/N), so that the
tolerance windows of neighbouring values just meet or overlap —
a ±5 % part family needs 24 values per decade (E24), a ±1 % family
needs 96 (E96) [6][8]:

| Series | Values/decade | Usual tolerance |
|---|---|---|
| E3 | 3 | ±20 % (and above) |
| E6 | 6 | ±20 % |
| E12 | 12 | ±10 % |
| E24 | 24 | ±5 % |
| E48 | 48 | ±2 % |
| E96 | 96 | ±1 % |

Two structural facts, verified against the published tables [6][7][8],
are used to keep the tables in `tables.py` typo-free:

- **E48 is every other value of E96** (with the third digit added in
  E48/E96 relative to E24), and **E12 is every other value of E24**,
  **E6 every other value of E12**. Only E24 and E96 are listed
  literally; the rest are derived, and unit tests assert the nesting
  and the lengths (3/6/12/24/48/96).
- E24 is *not* a subset of E48/E96: at three-digit precision some E24
  values are adjusted — E24's 2.7 has no exact E96 counterpart (E96
  carries 2.67 and 2.74 instead), and E24's 1.2 appears in E48 as
  1.21. The code therefore stores each series independently rather
  than "rounding" between them.

### How `encode` uses the series

`encode` (default `--series E24`) snaps the requested value to the
nearest preferred value of the chosen series, where "nearest" is the
distance on a log₁₀ scale — the correct metric for a geometric series,
since it compares ratios rather than absolute ohms. The snapped target
is then written with the significant digits the band count provides
(2 for 4-band, 3 for 5/6-band). If the target needs more digits than
the bands offer (an E96 target on a 4-band part), the closest
expressible value is used and the difference is reported, never hidden.
`--series exact` skips snapping entirely.

## 3. Temperature coefficient

The 6th band gives the temperature coefficient of resistance (TCR) in
ppm/K: the fractional change of resistance per kelvin,

ΔR/R = TCR × ΔT × 10⁻⁶,

so a 10 kΩ resistor with a brown (100 ppm/K) TCR band drifts
10 000 × 100 × 10⁻⁶ = 1 Ω per kelvin [4]. The tool reports the TCR;
applying it over a temperature range is left to the user (see
Limitations in the README).

## References

1. IEC. *IEC 60062:2016+AMD1:2019 CSV — Marking codes for resistors
   and capacitors.* IEC Webstore.
   https://webstore.iec.ch/en/publication/65655
2. IEC. *IEC 60062 Ed. 6.1 b:2019 (consolidated version).* ANSI
   Webstore (standard abstract and list of 2016 changes, incl. the new
   pink multiplier colour).
   https://webstore.ansi.org/standards/iec/iec60062ed2019
3. "Electronic color code." *The Free Dictionary Encyclopedia*
   (reproducing the IEC 60062:2016 Table: significant figures,
   multiplier, tolerance with letter codes, temperature coefficient
   with letter codes).
   https://encyclopedia.thefreedictionary.com/Electronic+color+code
4. Galco. "Resistor Color Code Calculator" (chart notes: colours,
   tolerances and temperature coefficients follow IEC 60062; standard
   values follow IEC 60063; 2016-edition additions).
   https://rdgateway.galco.com/engineering-calculators/resistor-color-code-calculator
5. All About Circuits. "Resistor Color Codes." *Textbook, Reference,
   Ch. 2* (band reading, E-series tables, IEC history).
   https://www.allaboutcircuits.com/TEXTBOOK/reference/chpt-2/resistor-color-codes/
6. EE Power. "Resistor Values — Resistor Standards and Codes."
   *Resistor Guide* (IEC 60063 preferred values; full E3–E96 tables).
   https://eepower.com/resistor-guide/resistor-standards-and-codes/resistor-values
7. Wevolver. "Resistor Chart: Comprehensive Guide to Resistor Values,
   E-Series, and Color Codes" (E-series per IEC 60063; tolerances per
   series).
   https://www.wevolver.com/article/resistor-chart-comprehensive-guide-to-resistor-values-e-series-and-color-codes
8. "Common resistor values (E-series decade tables)" — EIA/IEC decade
   table PDF (E24/E48/E96 listings used to cross-check the tables in
   code).
   https://2cc12256-1025-444a-bacb-901a9f007bda.filesusr.com/ugd/d1fcfc_1243465bcb494ec192538c8bca7e1cd8.pdf?index=true
