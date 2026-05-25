"""`python -m model_mirror` entrypoint."""

from __future__ import annotations

import sys

from model_mirror.cli import main


if __name__ == "__main__":
    sys.exit(main())
