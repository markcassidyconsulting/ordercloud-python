"""Allow running as ``python -m tools.codegen``."""

import sys

from .cli import main

sys.exit(main())
