#!/usr/bin/env python3
"""Entry point: decode/encode resistor colour bands.

    python3 resistor.py decode yellow violet red gold
    python3 resistor.py encode 4.7k --bands 5 --tolerance brown
    python3 resistor.py table

The implementation lives in ``src/resistor_color_code/``; this shim just
puts it on the import path so the project runs from a bare checkout with
nothing to install (pure standard library).
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
)

from resistor_color_code.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
