"""Enable `python -m wctracker`."""
from __future__ import annotations

import sys

from .cli import run

if __name__ == "__main__":
    sys.exit(run())
