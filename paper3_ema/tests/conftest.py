"""pytest suite for the Paper 3 standalone EMA module.

Run with:
    /home/user/.venv-ema/bin/python -m pytest paper3_ema/tests -q
or with the stdlib fallback:
    /home/user/.venv-ema/bin/python paper3_ema/tests/run_all.py
"""

from __future__ import annotations

import os
import sys

_PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)
