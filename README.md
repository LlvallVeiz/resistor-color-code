# Resistor Color Code

A resistor colour-code tool in **pure Python 3 (standard library only)** —
no dependencies, nothing to install. It works in both directions:
**decode** band colours into a value, and **encode** a value into band
colours, with a built-in IEC 60063 preferred-value (E-series) lookup and
a printable colour chart.

## Background

Through-hole resistors are marked with coloured bands defined by
**IEC 60062** ("Marking codes for resistors and capacitors"). Depending
on the band count, the bands carry two or three significant digits, a
power-of-ten multiplier, a tolerance, and — on 6-band parts — a
temperature coefficient:

```text
R  =  (significant digits as an integer) × 10^(multiplier exponent)
```

Manufactured values follow the **E-series of preferred numbers**
(**IEC 60063**): each series splits a decade into N geometric steps
(ratio 10^(1/N)) so the tolerance windows of neighbouring values just
tile the decade — E24 for ±5 % parts, E96 for ±1 % parts, and so on.
The full background, the colour/TCR tables, and where published charts
disagree (and which side this tool takes) are in
[docs/RESEARCH.md](docs/RESEARCH.md).

## What it does

- **Decode** 4-, 5- and 6-band colour sequences → resistance
  (Ω/kΩ/MΩ-formatted plus raw ohms), tolerance %, the value range the
  tolerance allows, and temperature coefficient (ppm/K) for 6-band.
- **Encode** a resistance → band colours. By default the value is
  first snapped to the nearest **E24** preferred value
  (`--series E3|E6|E12|E24|E48|E96`, or `--series exact` to disable
  snapping). The value the colours *actually* represent is always
  reported, including when a target needs more significant digits than
  the bands can express.
- **Table** subcommand prints the full IEC 60062 colour chart.
- Accepts value notations `4700`, `4.7k`, `4k7`, `1M`, `4R7`
  (RKM-style infix, per IEC 60062), colour aliases (`grey`, `purple`),
  and validates everything with specific, actionable error messages
  (unknown colour, gold in a digit position, leading black digit,
  wrong band count, …).

## How to run

```bash
# decode
python3 resistor.py decode yellow violet red gold
python3 resistor.py decode orange orange black black brown red   # 6-band

# encode (E24 snapping by default)
python3 resistor.py encode 4701
python3 resistor.py encode 4750 --bands 5 --tolerance brown --series E96
python3 resistor.py encode 10000 --series exact

# colour chart
python3 resistor.py table

# run the tests
python3 tests/test_resistor.py
```

## Example output

Real output from running the commands above (full log in
`examples/example_output.txt`):

```text
$ python3 resistor.py decode yellow violet red gold
Bands        : yellow violet red gold (4-band)
Resistance   : 4.7 kΩ (4700 Ω)
Tolerance    : ±5%
Range        : 4.46 kΩ … 4.93 kΩ

$ python3 resistor.py encode 4701
Requested    : 4.7 kΩ (4701 Ω)
E24 target   : 4.7 kΩ (4700 Ω) (nearest preferred value)
Bands        : yellow violet red gold (4-band)
Exact value  : 4.7 kΩ — the colours give exactly the target
Check (decode): 4.7 kΩ ±5%

$ python3 tests/test_resistor.py
All tests passed.
```

## Project structure

```text
resistor-color-code/
├── resistor.py                  # entry-point shim (puts src/ on the path)
├── src/resistor_color_code/
│   ├── __init__.py              # public API re-exports
│   ├── tables.py                # IEC 60062 colour tables + IEC 60063 E-series
│   ├── core.py                  # decode / encode / E-series lookup / chart
│   ├── values.py                # value parsing (4k7, 1M, …) and formatting
│   └── cli.py                   # argparse CLI: decode / encode / table
├── tests/test_resistor.py       # assert-based tests
├── examples/example_output.txt  # captured output of a real run
├── docs/RESEARCH.md             # standards background + references
├── LICENSE                      # MIT
└── README.md
```

## Design decisions

- **Pure standard library.** The domain is table lookups and small
  integer/float math; a dependency would add nothing. (Stated plainly,
  as required: there is deliberately no `requirements.txt`.)
- **E-series tables are derived, not transcribed.** Only E24 and E96
  are listed literally in `tables.py`; E48 = every other E96 value,
  E12 = every other E24 value, E6 = every other E12 value — nesting
  properties verified against the published tables. Tests assert the
  series lengths (3/6/12/24/48/96) and the nesting, so a transcription
  typo cannot slip through silently.
- **"Nearest" E-series value is measured on a log scale.** Preferred
  numbers are geometric; comparing ratios (log distance) picks the
  value a manufacturer would actually stock — e.g. 5000 Ω snaps to
  5.1 kΩ, not 4.7 kΩ.
- **Encode never hides rounding.** If the snapped target needs more
  significant digits than the band count offers (E96 target, 4-band
  part), the closest expressible value is chosen and the deviation is
  printed.
- **IEC 60062:2016 additions are in** — the pink ×0.001 multiplier and
  grey = 1 ppm/K temperature coefficient — while grey *tolerance*
  follows the widely printed ±0.05 % chart rather than the 2016
  ±0.01 % value; the reasoning is documented in
  [docs/RESEARCH.md](docs/RESEARCH.md).

## How it works

`core.decode` walks the band positions for the given band count,
converting digit colours to an integer and applying the multiplier
exponent; every band position is validated against the colours legal
there. `core.encode` snaps to the E-series (or takes the value as-is),
then searches multiplier exponents for the significant-digit integer
closest to the target, and maps digits back to colours. A decode of
the result is printed as a self-check. `values.parse_value` handles
plain, suffixed and RKM-infix notations with a single regex.

## Limitations & future work

- 3-band (legacy ±20 %) parts are not accepted; the layout is listed
  in the research doc.
- SMD codes (e.g. `472`, EIA-96 `01C`, `4R7` as a *printed* SMD code)
  are out of scope — only axial band colours are handled.
- The temperature coefficient is reported but not applied; a
  `--temp-range` drift calculator would be a natural extension.
- No tolerance *letter* codes (F/G/J/K…) are printed, though the
  mapping is documented in the research references.
- Colour perception is the user's problem: faded red/orange/brown
  bands are the classic misread — if a decode result is not a standard
  E-series value, suspect a misread band (the tool's E-series encode
  path makes this check easy).

## References

Full list with links in [docs/RESEARCH.md](docs/RESEARCH.md). Key
sources: IEC 60062:2016+AMD1:2019 (marking codes, IEC Webstore);
IEC 60063 preferred values via EE Power's *Resistor Guide* and
All About Circuits' *Resistor Color Codes*; the IEC 60062:2016 colour
table as reproduced in "Electronic color code" (The Free Dictionary
Encyclopedia).
