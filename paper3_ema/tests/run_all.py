"""Test runner entry point.

    /home/user/.venv-ema/bin/python paper3_ema/tests/run_all.py

Runs the offline suite via pytest.  pytest is the only test dependency
(`pip install pytest` — everything else in the package is stdlib); this file
is a convenience wrapper that installs nothing and reports clearly when
pytest is missing.
"""

from __future__ import annotations

import subprocess
import sys

HERE = __file__.rsplit("/", 1)[0]


def main() -> int:
    try:
        import pytest  # noqa: F401
    except ImportError:
        print("pytest is required for the test suite (pip install pytest).")
        print("Everything else in the EMA module is Python stdlib.")
        return 2
    return subprocess.call([sys.executable, "-m", "pytest", HERE, "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
