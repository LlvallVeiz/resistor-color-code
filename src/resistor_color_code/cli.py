"""Command-line interface: decode / encode / table subcommands."""

import argparse
import sys

from .core import color_chart, decode, encode
from .values import format_ohms, parse_value, raw_ohms


def _cmd_decode(args: argparse.Namespace) -> int:
    result = decode(args.colors)
    print(f"Bands        : {' '.join(args.colors)} ({result['bands']}-band)")
    print(f"Resistance   : {format_ohms(result['ohms'])} "
          f"({raw_ohms(result['ohms'])})")
    print(f"Tolerance    : ±{result['tolerance_pct']:g}%")
    lo = result["ohms"] * (1 - result["tolerance_pct"] / 100)
    hi = result["ohms"] * (1 + result["tolerance_pct"] / 100)
    print(f"Range        : {format_ohms(lo)} … {format_ohms(hi)}")
    if result["tempco_ppm"] is not None:
        print(f"Temp coeff   : {result['tempco_ppm']} ppm/K")
    return 0


def _cmd_encode(args: argparse.Namespace) -> int:
    result = encode(parse_value(args.value), bands=args.bands,
                    tolerance=args.tolerance, tempco=args.tempco,
                    series=args.series)
    req, target, exact = (result["requested_ohms"], result["target_ohms"],
                          result["exact_ohms"])
    print(f"Requested    : {format_ohms(req)} ({raw_ohms(req)})")
    if result["series"] != "exact":
        note = " (already a preferred value)" if target == req \
            else " (nearest preferred value)"
        print(f"{result['series']} target   : {format_ohms(target)} "
              f"({raw_ohms(target)}){note}")
    print(f"Bands        : {' '.join(result['colors'])} "
          f"({result['bands']}-band)")
    if exact == target:
        print(f"Exact value  : {format_ohms(exact)} — the colours give "
              f"exactly the target")
    else:
        off = (exact - target) / target * 100
        print(f"Exact value  : {format_ohms(exact)} ({raw_ohms(exact)}) — "
              f"closest the bands can express, off the target by "
              f"{off:+.2f}%")
    check = decode(result["colors"])
    print(f"Check (decode): {format_ohms(check['ohms'])} "
          f"±{check['tolerance_pct']:g}%"
          + (f", {check['tempco_ppm']} ppm/K"
             if check["tempco_ppm"] is not None else ""))
    return 0


def _cmd_table(args: argparse.Namespace) -> int:
    rows = color_chart()
    print("IEC 60062 colour chart")
    print(f"{'Colour':<8} {'Digit':>5} {'Multiplier':>10} "
          f"{'Tolerance':>10} {'Tempco (ppm/K)':>14}")
    print("-" * 51)
    for r in rows:
        print(f"{r['color']:<8} {r['digit']:>5} {r['multiplier']:>10} "
              f"{r['tolerance']:>10} {r['tempco']:>14}")
    print("No tolerance band at all means ±20%. "
          "Tempco is the 6th band, where fitted.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decode or encode resistor colour bands "
                    "(IEC 60062), with IEC 60063 E-series lookup."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dec = sub.add_parser("decode", help="colours -> resistance")
    p_dec.add_argument("colors", nargs="+",
                       help="4, 5 or 6 band colours, in order")
    p_dec.set_defaults(func=_cmd_decode)

    p_enc = sub.add_parser("encode", help="resistance -> colours")
    p_enc.add_argument("value",
                       help="resistance, e.g. 4700, 4.7k, 4k7, 1M, 4R7")
    p_enc.add_argument("--bands", type=int, default=4, choices=(4, 5, 6),
                       help="number of bands (default 4)")
    p_enc.add_argument("--tolerance", default="gold",
                       help="tolerance colour (default gold = ±5%%); "
                            "'none' for ±20%%")
    p_enc.add_argument("--tempco", default="red",
                       help="temperature-coefficient colour for 6-band "
                            "(default red = 50 ppm/K)")
    p_enc.add_argument("--series", default="E24",
                       choices=("E3", "E6", "E12", "E24", "E48", "E96",
                                "exact"),
                       help="snap to this IEC 60063 preferred-value "
                            "series first (default E24); 'exact' disables "
                            "snapping")
    p_enc.set_defaults(func=_cmd_encode)

    p_tab = sub.add_parser("table", help="print the colour chart")
    p_tab.set_defaults(func=_cmd_table)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
